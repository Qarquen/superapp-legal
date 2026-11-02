"""EPİAŞ saatlik PTF verisini yükler, yayınlanmış değerlerle doğrular, temel istatistikleri çıkarır."""
import glob, sys
import pandas as pd

VERI = sys.argv[1]  # oskkee/epias-ptf-data klasörü


def yukle(dosya):
    df = pd.read_csv(dosya, sep=";", dtype=str)
    df["zaman"] = pd.to_datetime(df["Tarih"] + " " + df["Saat"], format="%d.%m.%Y %H:%M")
    df["ptf"] = df["PTF (TL/MWh)"].str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float)
    return df[["zaman", "ptf"]]


ptf = (pd.concat([yukle(f) for f in sorted(glob.glob(f"{VERI}/Piyasa_Takas_Fiyati-*.csv"))])
       .drop_duplicates("zaman").sort_values("zaman").set_index("zaman")["ptf"])
ptf.to_frame().to_parquet("/home/user/superapp-legal/bess-20mw/analiz/ptf_saatlik.parquet") if False else None
ptf.to_csv("/home/user/superapp-legal/bess-20mw/analiz/ptf_saatlik.csv")

print(f"Kapsam: {ptf.index.min()} -> {ptf.index.max()} | {len(ptf):,} saat | eksik/tekrarsız kontrol: {ptf.index.is_unique}")

print("\n=== DOĞRULAMA (yayınlanmış değerler) ===")
tem25 = ptf["2025-07"].mean()
print(f"Temmuz 2025 ortalama PTF: {tem25:,.2f}  | Montel/Foreks: 2.965,16  | fark {tem25-2965.16:+.2f}")
y25 = ptf["2025"]
print(f"2025 takvim yılı saat sayısı: {len(y25):,} | PTF < 1.500 TL/MWh saat sayısı: {(y25 < 1500).sum():,}  | santral verisi: 889")
print(f"Azami fiyat (tavan) 2025-26: {ptf['2025-04-25':].max():,.2f} | asgari: {ptf['2025-04-25':].min():,.2f}")

print("\n=== SON 12 AY (25.04.2025-25.04.2026) ===")
s = ptf["2025-04-25":"2026-04-25"]
print(f"Ortalama: {s.mean():,.0f} TL/MWh | 0 TL saat: {(s <= 0.01).sum()} | <500 TL saat: {(s < 500).sum()} | <1.500: {(s < 1500).sum()}")
g = s.groupby(s.index.date)
def bant(x, n):
    v = x.sort_values().values
    return v[-n:].mean() - v[:n].mean()
spread2 = g.apply(lambda x: bant(x, 2))
spread4 = g.apply(lambda x: bant(x, 4))
print(f"Günlük spread (en pahalı 2 saat - en ucuz 2 saat): ort {spread2.mean():,.0f}, medyan {spread2.median():,.0f}, p10 {spread2.quantile(.1):,.0f}, p90 {spread2.quantile(.9):,.0f}")
print(f"Günlük spread (4 saatlik bant): ort {spread4.mean():,.0f}")
aylik = s.groupby(s.index.to_period("M")).agg(["mean", "min", "max"])
aylik["spread2"] = spread2.groupby(pd.to_datetime(spread2.index).to_period("M")).mean()
print("\nAylık: ortalama / en düşük / en yüksek / günlük 2s spread ortalaması")
print(aylik.round(0).to_string())
saat = s.groupby(s.index.hour).mean()
print("\nGünün saatlerine göre ortalama PTF:")
print(" ".join(f"{h:02d}:{v:,.0f}" for h, v in saat.items()))
marj = (s - 1500).clip(lower=0)
print(f"\nSantral marjı (PTF-1.500, negatifse 0) ortalaması: {marj.mean():,.0f} TL/MWh -> 1 MW için yıllık {marj.sum()/1e6:,.2f} milyon TL")
