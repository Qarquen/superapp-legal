"""20 MW BESS: gerçek saatlik PTF ile SFK + arbitraj ortak optimizasyonu (LP, HiGHS).

SFK enerji kuralı (TEİAŞ depolama kriterleri, ikincil kaynak): T saatlik teklif bloğunda
rezerv r MW için enerji >= r x T x 2 (çift yön) x 1,125  ->  SoC her saat [1,125*T*r, E - 1,125*T*r] bandında.
"""
import json, sys, time
import pandas as pd, pulp

PTF = pd.read_csv("/home/user/superapp-legal/bess-20mw/analiz/ptf_saatlik.csv", index_col=0, parse_dates=True)["ptf"]
p = PTF["2025-04-25":"2026-04-24"].values  # son 12 ay, 8.760 saat
assert len(p) == 8760, len(p)

KUR, CE, CP = 50.0, 95, 170           # TL/USD, USD/kWh, USD/kW (varsayım)
RTE = 0.88; ETA = RTE ** 0.5
AVAIL = 6500 / 8760                   # SFK'da geçen saat oranı (ihale kazanma + kullanılabilirlik)
CAPTURE = 0.85                        # arbitrajda kusursuz öngörüden gerçekçiye geçiş
DEG = CE * 1000 * KUR / 6000          # TL/MWh deşarj: enerji CAPEX / 6.000 çevrim
OM, SYS = 0.04, 5e6


def coz(P, E, T, sfk_fiyat, bant=None):
    import highspy, numpy as np
    n = len(p); B = n // T
    bant = 1.125 * T if bant is None else bant  # MW başına SoC payı (her yön)
    h = highspy.Highs(); h.setOptionValue("output_flag", False)
    inf = highspy.kHighsInf
    # değişken sırası: c[0..n), d[0..n), s[0..n), r[0..B)
    ic, id_, is_, ir = 0, n, 2 * n, 3 * n
    nv = 3 * n + B
    obj = np.zeros(nv); lb = np.zeros(nv); ub = np.zeros(nv)
    obj[ic:ic + n] = -CAPTURE * p; obj[id_:id_ + n] = CAPTURE * p - DEG
    obj[ir:ir + B] = T * sfk_fiyat * AVAIL
    ub[ic:id_] = P; ub[id_:is_] = P; ub[is_:ir] = E; ub[ir:] = P
    h.addVars(nv, lb, ub)
    h.changeColsCost(nv, np.arange(nv, dtype=np.int32), obj)
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)
    rows_lo, rows_hi, starts, idx, val = [], [], [], [], []
    def row(lo, hi, cols, coefs):
        starts.append(len(idx)); idx.extend(cols); val.extend(coefs); rows_lo.append(lo); rows_hi.append(hi)
    for t in range(n):
        rb = ir + t // T
        # s_t - s_{t-1} - ETA c_t + d_t/ETA = 0  (t=0: s_{-1}=E/2)
        if t == 0:
            row(E / 2, E / 2, [is_, ic, id_], [1, -ETA, 1 / ETA])
        else:
            row(0, 0, [is_ + t, is_ + t - 1, ic + t, id_ + t], [1, -1, -ETA, 1 / ETA])
        row(-inf, P, [id_ + t, rb], [1, 1])
        row(-inf, P, [ic + t, rb], [1, 1])
        row(0, inf, [is_ + t, rb], [1, -bant])
        row(-inf, E, [is_ + t, rb], [1, bant])
    row(E / 2, E / 2, [is_ + n - 1], [1])
    h.addRows(len(rows_lo), np.array(rows_lo), np.array(rows_hi), len(idx),
              np.array(starts, dtype=np.int32), np.array(idx, dtype=np.int32), np.array(val))
    h.run()
    assert h.modelStatusToString(h.getModelStatus()) == "Optimal", h.modelStatusToString(h.getModelStatus())
    x = np.array(h.getSolution().col_value)
    cv, dv, rv = x[ic:id_], x[id_:is_], x[ir:]
    arb_brut = float(np.dot(p, dv - cv)); desarj = float(dv.sum())
    sfk_gelir = float(rv.sum()) * T * sfk_fiyat * AVAIL
    capex_tl = (E * 1000 * CE + P * 1000 * CP) * KUR
    arb_net = CAPTURE * arb_brut - DEG * desarj
    net = sfk_gelir + arb_net - capex_tl * OM - SYS
    return dict(P=P, E=E, T=T, sfk_fiyat=sfk_fiyat,
                capex_musd=round(capex_tl / KUR / 1e6, 3), capex_mtl=round(capex_tl / 1e6, 1),
                sfk_mw_ort=round(float(rv.mean()), 2), sfk_mw_kural=round(min(P, E / (2 * bant)), 2),
                sfk_gelir_mtl=round(sfk_gelir / 1e6, 2), arb_net_mtl=round(arb_net / 1e6, 2),
                dongu=round(desarj / E, 0), opex_mtl=round((capex_tl * OM + SYS) / 1e6, 2),
                net_mtl=round(net / 1e6, 2), geri_odeme=round(capex_tl / net, 2) if net > 0 else None)


# (ad, güç MW, enerji MWh, blok saat, kapasite fiyatı TL/MW-saat, SoC payı/MW/yön)
PFK = 0.625  # PFK: enerji/rezerv >= 1,25 -> her yöne 0,625 saat
senaryolar = [
    ("P1 PFK 20 MW / 40 MWh", 20, 40, 1, 1879, PFK),
    ("P2 PFK 20 MW / 40 MWh, fiyat 669 (2025)", 20, 40, 1, 669, PFK),
    ("P3 PFK 20 MW / 40 MWh, fiyat 3.000", 20, 40, 1, 3000, PFK),
    ("P4 PFK 20 MW / 25 MWh", 20, 25, 1, 1879, PFK),
    ("S1 SFK 10 MW / 90 MWh", 10, 90, 4, 2000, None),
    ("S2 SFK 20 MW / 180 MWh", 20, 180, 4, 2000, None),
    ("S0 SFK 20 MW / 40 MWh (eski sunum)", 20, 40, 4, 2000, None),
    ("A0 yalnız al-sat 20 MW / 40 MWh", 20, 40, 4, 0, None),
]
sonuc = []
for ad, P, E, T, f, bnt in senaryolar:
    t0 = time.time(); r = coz(P, E, T, f, bnt); r["senaryo"] = ad; sonuc.append(r)
    print(f"{ad:<44} SFK ort {r['sfk_mw_ort']:>5} MW (kural {r['sfk_mw_kural']:>5}) | SFK {r['sfk_gelir_mtl']:>7} | arb {r['arb_net_mtl']:>6} | "
          f"döngü {r['dongu']:>4} | CAPEX {r['capex_mtl']:>6} M TL | net {r['net_mtl']:>7} | geri ödeme {r['geri_odeme']} yıl  ({time.time()-t0:.0f}s)", flush=True)
json.dump(sonuc, open("/home/user/superapp-legal/bess-20mw/analiz/optimizasyon_sonuclari.json", "w"), ensure_ascii=False, indent=1)
