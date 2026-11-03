"""
Santral + batarya (BESS) portföy analizi — tek dosya, kendi başına çalışır.

Ne yapar?
  1. EPİAŞ'tan indirdiğin saatlik PTF dosyasını okur ve özet istatistik çıkarır.
  2. Santral ile bataryayı yılın her saati için birlikte optimize eder (doğrusal programlama, HiGHS):
       - Santral: 250–350 MW arası çalışır, elektrik satar, sekonder (SFK) yedek tutabilir.
       - Batarya: primer (PFK), sekonder (SFK) ve al-sat yapabilir.
       - Bağlantı: santral + batarya, tüm yukarı yedekler devreye girse bile 370 MW'ı aşamaz.
       - TEİAŞ enerji kuralı: primer için 1 MW başına 1,25 MWh, sekonder için 1 MW başına
         blok saati x 2 yön x 1,125 MWh (4 saatlik blokta 9 MWh).
  3. Senaryoları çalıştırır, bataryanın katkısını ve geri ödemesini hesaplar.
  4. 5 yıl geri ödeme için gereken primer fiyatını (eşik) bulur.
  5. Sonuçları ekrana yazar ve Excel'e kaydeder.

Kurulum (bir kere):
    pip install pandas numpy highspy openpyxl

Veri:
    EPİAŞ Şeffaflık Platformu > Elektrik > Gün Öncesi Piyasası > Piyasa Takas Fiyatı (PTF)
    Saatlik, bir yıllık aralık seç ve CSV indir. Dosya şöyle başlar:
        Tarih;Saat;PTF (TL/MWh);PTF (USD/MWh);PTF (EUR/MWh)
        25.04.2025;00:00;2.950,00;77,36;67,30

Çalıştırma:
    python bess_analiz.py --veri Piyasa_Takas_Fiyati-25042025-25042026.csv
    python bess_analiz.py --veri dosya1.csv dosya2.csv --baslangic 2025-04-25 --bitis 2026-04-24

Değiştirmek istediğin varsayımlar aşağıdaki VARSAYIMLAR sözlüğünde.
"""
import argparse

import highspy
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# VARSAYIMLAR — burayı kendi verinle değiştir
# ---------------------------------------------------------------------------
VARSAYIMLAR = {
    # Santral
    "santral_max_mw": 350,        # tam yük
    "santral_min_mw": 250,        # yük düştüğünde
    "santral_mc": 1500,           # marjinal maliyet, TL/MWh (PTF bunun altına inince yük düşüyor)
    "baglanti_limit_mw": 370,     # bağlantı / lisans sınırı
    # Fiyatlar
    "pfk_fiyat": 1879,            # primer, TL/MW-saat (ZAYIF KAYNAK — TEİAŞ serisiyle değiştir)
    "sfk_fiyat": 2000,            # sekonder, TL/MW-saat (EPİAŞ 2026 haftalık: 1.112–4.701)
    "kullanilabilirlik": 6500 / 8760,  # yedeğin satılabildiği saat oranı
    "alsat_yakalama": 0.85,       # kusursuz öngörüden gerçekçiye geçiş
    # Batarya maliyetleri
    "kur": 50.0,                  # TL/USD
    "enerji_usd_kwh": 95,         # tahmin, teklif değil
    "guc_usd_kw": 170,            # tahmin, teklif değil
    "verim": 0.88,                # çevrim verimi (AC-AC)
    "cevrim_omru": 6000,          # aşınma maliyeti için
    "bakim_orani": 0.04,          # yatırımın %'si / yıl
    "sistem_gideri_mtl": 5.0,     # sistem kullanım + dengesizlik, M TL / yıl (tahmin)
    # TEİAŞ kuralları
    "sfk_blok_saat": 4,
    "pfk_enerji_orani": 1.25,     # MWh / MW
    "sfk_guvenlik": 1.125,
    # Hedef
    "hedef_geri_odeme": 5.0,
}


# ---------------------------------------------------------------------------
# 1) Veri
# ---------------------------------------------------------------------------
def ptf_yukle(dosyalar):
    """EPİAŞ CSV'lerini okur, Türkçe sayı biçimini (2.950,00) çevirir, saatlik seri döndürür."""
    parcalar = []
    for f in dosyalar:
        df = pd.read_csv(f, sep=";", dtype=str)
        zaman = pd.to_datetime(df["Tarih"] + " " + df["Saat"], format="%d.%m.%Y %H:%M")
        fiyat = df["PTF (TL/MWh)"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
        parcalar.append(pd.Series(fiyat.values, index=zaman))
    ptf = pd.concat(parcalar).sort_index()
    return ptf[~ptf.index.duplicated()]


def ozet_yaz(ptf, v):
    print(f"Veri: {ptf.index.min():%d.%m.%Y} – {ptf.index.max():%d.%m.%Y}, {len(ptf):,} saat")
    print(f"  Ortalama PTF          : {ptf.mean():,.0f} TL/MWh   (en düşük {ptf.min():,.0f}, en yüksek {ptf.max():,.0f})")
    print(f"  PTF < {v['santral_mc']:,} olan saat : {(ptf < v['santral_mc']).sum():,}   (santralin yük düşürdüğü saatler)")
    gunluk = ptf.groupby(ptf.index.date).apply(lambda x: x.nlargest(2).mean() - x.nsmallest(2).mean())
    print(f"  Günlük spread (2 saat): ortalama {gunluk.mean():,.0f}, medyan {gunluk.median():,.0f} TL/MWh")
    marj = (ptf - v["santral_mc"]).clip(lower=0)
    print(f"  Santral marjı ort.    : {marj.mean():,.0f} TL/MWh  (max(PTF − marjinal maliyet; 0))")


# ---------------------------------------------------------------------------
# 2) Optimizasyon
# ---------------------------------------------------------------------------
def coz(p, v, batarya_mw, batarya_mwh, santral_sfk=True, pfk_pazar_max=None, **degisiklik):
    """Bir senaryoyu çözer. degisiklik ile VARSAYIMLAR'dan herhangi biri geçici olarak değiştirilebilir,
    örn. coz(p, V, 20, 40, pfk_fiyat=669)."""
    v = {**v, **degisiklik}
    n, T = len(p), v["sfk_blok_saat"]
    B = n // T
    p = np.asarray(p[: B * T], dtype=float); n = len(p)
    Pb, E = float(batarya_mw), float(batarya_mwh)
    eta = v["verim"] ** 0.5
    asinma = v["enerji_usd_kwh"] * 1000 * v["kur"] / v["cevrim_omru"]      # TL / MWh deşarj
    pfk_pay = v["pfk_enerji_orani"] / 2                                      # her yön için MWh / MW
    sfk_pay = v["sfk_guvenlik"] * T                                          # her yön için MWh / MW
    av = v["kullanilabilirlik"]

    # Değişken sırası: g (santral), c (şarj), d (deşarj), s (doluluk), rp (primer) | rs (bat. sekonder), sp (santral sekonder)
    ig, ic, id_, is_, irp = 0, n, 2 * n, 3 * n, 4 * n
    irs, isp = 5 * n, 5 * n + B
    nv = 5 * n + 2 * B
    alt, ust, kar = np.zeros(nv), np.zeros(nv), np.zeros(nv)
    alt[ig:ic], ust[ig:ic], kar[ig:ic] = v["santral_min_mw"], v["santral_max_mw"], p - v["santral_mc"]
    ust[ic:id_], kar[ic:id_] = Pb, -v["alsat_yakalama"] * p
    ust[id_:is_], kar[id_:is_] = Pb, v["alsat_yakalama"] * p - asinma
    ust[is_:irp] = E
    ust[irp:irs], kar[irp:irs] = min(Pb, pfk_pazar_max if pfk_pazar_max is not None else Pb), v["pfk_fiyat"] * av
    ust[irs:isp], kar[irs:isp] = Pb, T * v["sfk_fiyat"] * av
    ust[isp:] = (v["santral_max_mw"] - v["santral_min_mw"]) / 2 if santral_sfk else 0
    kar[isp:] = T * v["sfk_fiyat"] * av

    h = highspy.Highs(); h.setOptionValue("output_flag", False); inf = highspy.kHighsInf
    h.addVars(nv, alt, ust)
    h.changeColsCost(nv, np.arange(nv, dtype=np.int32), kar)
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)

    lo, hi, bas, sut, kat = [], [], [], [], []
    def kisit(a, b, kolonlar, katsayilar):
        bas.append(len(sut)); sut.extend(kolonlar); kat.extend(katsayilar); lo.append(a); hi.append(b)

    for t in range(n):
        b = t // T
        if t == 0:   # doluluk dengesi, yarı dolu başlar
            kisit(E / 2, E / 2, [is_, ic, id_], [1, -eta, 1 / eta])
        else:
            kisit(0, 0, [is_ + t, is_ + t - 1, ic + t, id_ + t], [1, -1, -eta, 1 / eta])
        kisit(-inf, v["santral_max_mw"], [ig + t, isp + b], [1, 1])            # santral + yukarı yedek <= 350
        kisit(v["santral_min_mw"], inf, [ig + t, isp + b], [1, -1])           # santral − aşağı yedek >= 250
        kisit(-inf, v["baglanti_limit_mw"], [ig + t, isp + b, id_ + t, irp + t, irs + b], [1, 1, 1, 1, 1])  # 370 MW
        kisit(-inf, Pb, [id_ + t, irp + t, irs + b], [1, 1, 1])               # batarya güç (deşarj yönü)
        kisit(-inf, Pb, [ic + t, irp + t, irs + b], [1, 1, 1])                # batarya güç (şarj yönü)
        kisit(0, inf, [is_ + t, irp + t, irs + b], [1, -pfk_pay, -sfk_pay])   # yedek için alt enerji payı
        kisit(-inf, E, [is_ + t, irp + t, irs + b], [1, pfk_pay, sfk_pay])    # yedek için üst enerji payı
    kisit(E / 2, E / 2, [is_ + n - 1], [1])                                   # yıl sonunda yine yarı dolu
    h.addRows(len(lo), np.array(lo), np.array(hi), len(sut),
              np.array(bas, dtype=np.int32), np.array(sut, dtype=np.int32), np.array(kat))
    h.run()
    durum = h.modelStatusToString(h.getModelStatus())
    if durum != "Optimal":
        raise RuntimeError(f"Çözüm bulunamadı: {durum}")

    x = np.array(h.getSolution().col_value)
    g, c, d = x[ig:ic], x[ic:id_], x[id_:is_]
    rp, rs, sp = x[irp:irs], x[irs:isp], x[isp:]
    # Referans: santral tek başına, yan hizmetsiz (fiyat > MC ise tam yük, değilse min yük)
    referans = np.sum((p - v["santral_mc"]) * np.where(p > v["santral_mc"], v["santral_max_mw"], v["santral_min_mw"]))
    yatirim = (E * 1000 * v["enerji_usd_kwh"] + Pb * 1000 * v["guc_usd_kw"]) * v["kur"] / 1e6
    gider = yatirim * v["bakim_orani"] + (v["sistem_gideri_mtl"] if Pb > 0 else 0)
    artis = (h.getInfo().objective_function_value - referans) / 1e6
    return {
        "batarya": f"{Pb:g} MW / {E:g} MWh",
        "yatirim_mtl": yatirim,
        "primer_mtl": rp.sum() * v["pfk_fiyat"] * av / 1e6,
        "batarya_sekonder_mtl": rs.sum() * T * v["sfk_fiyat"] * av / 1e6,
        "santral_sekonder_mtl": sp.sum() * T * v["sfk_fiyat"] * av / 1e6,
        "santral_enerji_degisim_mtl": (np.sum((p - v["santral_mc"]) * g) - referans) / 1e6,
        "alsat_mtl": (v["alsat_yakalama"] * np.dot(p, d - c) - asinma * d.sum()) / 1e6,
        "batarya_gideri_mtl": gider,
        "portfoy_net_mtl": artis - gider,
        "ort_primer_mw": rp.mean(),
        "ort_santral_sekonder_mw": sp.mean(),
    }


# ---------------------------------------------------------------------------
# 3) Senaryolar ve eşik
# ---------------------------------------------------------------------------
def senaryolari_calistir(p, v):
    ref = coz(p, v, 0, 0)                         # bataryasız: yalnız santral sekonderi
    ref_ucuz_sfk = coz(p, v, 0, 0, sfk_fiyat=1112)
    senaryolar = [
        ("Bataryasız: yalnız santral sekonderi", dict(batarya_mw=0, batarya_mwh=0), None),
        ("Önerilen: 20 MW / 40 MWh", dict(batarya_mw=20, batarya_mwh=40), ref),
        ("Ucuz enerji: 20 MW / 25 MWh", dict(batarya_mw=20, batarya_mwh=25), ref),
        ("Güvenli pay: 20 MW / 30 MWh", dict(batarya_mw=20, batarya_mwh=30), ref),
        ("Büyük: 40 MW / 50 MWh", dict(batarya_mw=40, batarya_mwh=50), ref),
        ("100 MW / 125 MWh (pazar 100 MW alırsa)", dict(batarya_mw=100, batarya_mwh=125), ref),
        ("100 MW / 200 MWh, primer pazarı 20 MW", dict(batarya_mw=100, batarya_mwh=200, pfk_pazar_max=20), ref),
        ("Primer pazarı yalnız 10 MW", dict(batarya_mw=20, batarya_mwh=40, pfk_pazar_max=10), ref),
        ("Primer 669 (2025 ilk çeyrek)", dict(batarya_mw=20, batarya_mwh=40, pfk_fiyat=669), ref),
        ("Sekonder 1.112 (2026 en düşük)", dict(batarya_mw=20, batarya_mwh=40, sfk_fiyat=1112), ref_ucuz_sfk),
        ("Primer 669 + sekonder 1.112", dict(batarya_mw=20, batarya_mwh=40, pfk_fiyat=669, sfk_fiyat=1112), ref_ucuz_sfk),
        ("Kur 62", dict(batarya_mw=20, batarya_mwh=40, kur=62), ref),
    ]
    satirlar = []
    for ad, kw, referans in senaryolar:
        r = ref if referans is None else coz(p, v, **kw)
        katki = r["portfoy_net_mtl"] - (referans["portfoy_net_mtl"] if referans else 0)
        r.update(senaryo=ad, batarya_katkisi_mtl=katki if referans else None,
                 geri_odeme_yil=(r["yatirim_mtl"] / katki) if referans and katki > 0 else None)
        satirlar.append(r)
        go = f"{r['geri_odeme_yil']:.1f} yıl" if r["geri_odeme_yil"] else "—"
        kt = f"{katki:7.1f}" if referans else "      —"
        print(f"  {ad:<42} yatırım {r['yatirim_mtl']:7.1f} | portföy net {r['portfoy_net_mtl']:7.1f} | batarya katkısı {kt} | geri ödeme {go}")
    return pd.DataFrame(satirlar).set_index("senaryo")


def esik_bul(p, v, mw=20, mwh=40, alt=100, ust=3000, adim=12):
    """Bataryanın geri ödemesi tam hedef süreye eşit olduğu primer fiyatını ikiye bölme yöntemiyle bulur."""
    ref = coz(p, v, 0, 0)["portfoy_net_mtl"]
    hedef = v["hedef_geri_odeme"]
    for _ in range(adim):
        orta = (alt + ust) / 2
        r = coz(p, v, mw, mwh, pfk_fiyat=orta)
        katki = r["portfoy_net_mtl"] - ref
        geri = r["yatirim_mtl"] / katki if katki > 0 else 99
        alt, ust = (orta, ust) if geri > hedef else (alt, orta)
    return (alt + ust) / 2


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Santral + batarya portföy analizi")
    ap.add_argument("--veri", nargs="+", required=True, help="EPİAŞ PTF CSV dosya(lar)ı")
    ap.add_argument("--baslangic", help="örn. 2025-04-25 (boşsa son 8.760 saat)")
    ap.add_argument("--bitis", help="örn. 2026-04-24")
    ap.add_argument("--cikti", default="bess_sonuclar.xlsx", help="Excel çıktı dosyası")
    ap.add_argument("--esik", action="store_true", help="5 yıl için gereken primer fiyatını da hesapla (birkaç dakika)")
    a = ap.parse_args()

    v = VARSAYIMLAR
    ptf = ptf_yukle(a.veri)
    if a.baslangic or a.bitis:
        ptf = ptf[a.baslangic:a.bitis]
    else:
        ptf = ptf.iloc[-8760:]
    print("\n=== 1) VERİ ÖZETİ ==="); ozet_yaz(ptf, v)

    print("\n=== 2) SENARYOLAR (M TL / yıl) ===")
    sonuc = senaryolari_calistir(ptf.values, v)

    if a.esik:
        print("\n=== 3) EŞİK ===")
        e = esik_bul(ptf.values, v)
        print(f"  {v['hedef_geri_odeme']:.0f} yıl geri ödeme için gereken primer fiyatı: ≈{e:,.0f} TL/MW-saat")
        sonuc.attrs["esik"] = e

    with pd.ExcelWriter(a.cikti) as w:
        sonuc.round(2).to_excel(w, sheet_name="Senaryolar")
        pd.Series(v, name="deger").to_frame().to_excel(w, sheet_name="Varsayimlar")
    print(f"\nSonuçlar kaydedildi: {a.cikti}")


if __name__ == "__main__":
    main()
