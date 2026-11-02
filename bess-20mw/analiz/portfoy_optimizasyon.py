"""Santral + batarya portföy optimizasyonu (HiGHS LP), gerçek saatlik PTF, 25.04.2025–24.04.2026.

Santral: 250–350 MW (yük 100 MW düşebiliyor), marjinal maliyet 1.500 TL/MWh, sekonder (SFK) teklif edebilir.
Batarya: primer (PFK, saatlik), sekonder (SFK, 4 saatlik blok), al-sat.
Bağlantı: santral + batarya, tüm yukarı yedekler devreye girse bile 370 MW'ı aşamaz.
Değer = portföy kârı − bugünkü durum (santral tek başına, yan hizmetsiz).
"""
import json
import numpy as np, pandas as pd, highspy

p = pd.read_csv("ptf_saatlik.csv", index_col=0, parse_dates=True)["ptf"]["2025-04-25":"2026-04-24"].values
n, T = len(p), 4
B = n // T
MC, GMAX, GMIN, LIM = 1500, 350, 250, 370
AV, CAPT, CE, CP, OM, SYS = 6500 / 8760, 0.85, 95, 170, 0.04, 5.0


def coz(Pb, E, pfk=1879, sfk=2000, kur=50, santral_sfk=True, pfk_max=1e9, sfk_max=1e9):
    deg = CE * 1000 * kur / 6000
    h = highspy.Highs(); h.setOptionValue("output_flag", False); inf = highspy.kHighsInf
    # sıra: g, c, d, s, rp (saatlik) | rs, sp (blok)
    ig, ic, id_, is_, irp = 0, n, 2 * n, 3 * n, 4 * n
    irs, isp = 5 * n, 5 * n + B
    nv = 5 * n + 2 * B
    lb = np.zeros(nv); ub = np.zeros(nv); cost = np.zeros(nv)
    lb[ig:ic] = GMIN; ub[ig:ic] = GMAX; cost[ig:ic] = p - MC
    ub[ic:id_] = Pb; cost[ic:id_] = -CAPT * p
    ub[id_:is_] = Pb; cost[id_:is_] = CAPT * p - deg
    ub[is_:irp] = E
    ub[irp:irs] = min(Pb, pfk_max); cost[irp:irs] = pfk * AV
    ub[irs:isp] = min(Pb, sfk_max); cost[irs:isp] = T * sfk * AV
    ub[isp:] = (GMAX - GMIN) / 2 if santral_sfk else 0; cost[isp:] = T * sfk * AV
    h.addVars(nv, lb, ub); h.changeColsCost(nv, np.arange(nv, dtype=np.int32), cost)
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)
    lo, hi, st, ix, vl = [], [], [], [], []
    def row(a, b, cols, coefs):
        st.append(len(ix)); ix.extend(cols); vl.extend(coefs); lo.append(a); hi.append(b)
    eta = 0.88 ** 0.5
    for t in range(n):
        b = t // T
        if t == 0: row(E / 2, E / 2, [is_, ic, id_], [1, -eta, 1 / eta])
        else: row(0, 0, [is_ + t, is_ + t - 1, ic + t, id_ + t], [1, -1, -eta, 1 / eta])
        row(-inf, GMAX, [ig + t, isp + b], [1, 1])                       # santral üst
        row(GMIN, inf, [ig + t, isp + b], [1, -1])                       # santral alt (aşağı yedek)
        row(-inf, LIM, [ig + t, isp + b, id_ + t, irp + t, irs + b], [1, 1, 1, 1, 1])  # 370 MW
        row(-inf, Pb, [id_ + t, irp + t, irs + b], [1, 1, 1])
        row(-inf, Pb, [ic + t, irp + t, irs + b], [1, 1, 1])
        row(0, inf, [is_ + t, irp + t, irs + b], [1, -0.625, -1.125 * T])
        row(-inf, E, [is_ + t, irp + t, irs + b], [1, 0.625, 1.125 * T])
    row(E / 2, E / 2, [is_ + n - 1], [1])
    h.addRows(len(lo), np.array(lo), np.array(hi), len(ix), np.array(st, dtype=np.int32), np.array(ix, dtype=np.int32), np.array(vl))
    h.run(); assert h.modelStatusToString(h.getModelStatus()) == "Optimal"
    x = np.array(h.getSolution().col_value); obj = h.getInfo().objective_function_value
    g, c, d = x[ig:ic], x[ic:id_], x[id_:is_]; rp, rs, sp = x[irp:irs], x[irs:isp], x[isp:]
    base = np.sum((p - MC) * np.where(p > MC, GMAX, GMIN))
    capex = (E * 1000 * CE + Pb * 1000 * CP) * kur / 1e6
    r = dict(
        batarya=f"{Pb}/{E}", capex=round(capex, 1),
        pfk_gelir=round(rp.sum() * pfk * AV / 1e6, 1), bat_sfk_gelir=round(rs.sum() * T * sfk * AV / 1e6, 1),
        santral_sfk_gelir=round(sp.sum() * T * sfk * AV / 1e6, 1),
        alsat=round((CAPT * np.dot(p, d - c) - deg * d.sum()) / 1e6, 1),
        santral_enerji_degisim=round((np.sum((p - MC) * g) - base) / 1e6, 1),
        artis=round((obj - base) / 1e6, 1),
        pfk_mw_ort=round(rp.mean(), 1), santral_sfk_mw_ort=round(sp.mean(), 1), santral_ort_mw=round(g.mean(), 1))
    r["bat_opex"] = round(capex * OM + (SYS if Pb > 0 else 0), 1)
    r["net"] = round(r["artis"] - r["bat_opex"], 1)
    r["geri_odeme"] = round(capex / r["net"], 2) if capex > 0 and r["net"] > 0 else None
    aug = E * 1000 * CE * 0.15 * kur / 1e6
    akis = [-capex] + [r["net"] - (aug if y == 8 else 0) for y in range(1, 16)]
    r["npv"] = round(sum(a / 1.1 ** i for i, a in enumerate(akis)), 0)
    lo_, hi_ = -0.99, 50.0
    if capex > 0:
        for _ in range(200):
            m = (lo_ + hi_) / 2
            v = sum(a / (1 + m) ** i for i, a in enumerate(akis))
            lo_, hi_ = (m, hi_) if v > 0 else (lo_, m)
        r["irr"] = round(m * 100, 1)
    return r


S = [
    ("S1 Yalnız santral sekonder (bataryasız)", dict(Pb=0, E=0)),
    ("S2 Batarya 20/40, santral sekonder yok", dict(Pb=20, E=40, santral_sfk=False)),
    ("S3 ÖNERİLEN: batarya 20/40 + santral sekonder", dict(Pb=20, E=40)),
    ("S4 Ucuz enerji: batarya 20/25 + santral sekonder", dict(Pb=20, E=25)),
    ("S5 Büyük: batarya 40/50 + santral sekonder", dict(Pb=40, E=50)),
    ("S6 Daha büyük: batarya 50/63 + santral sekonder", dict(Pb=50, E=63)),
    ("S7 S3, PFK pazarı 10 MW ile sınırlı", dict(Pb=20, E=40, pfk_max=10)),
    ("D1 S3, PFK 669 (2025 seviyesi)", dict(Pb=20, E=40, pfk=669)),
    ("D2 S3, SFK 1.112 (2026 en düşük)", dict(Pb=20, E=40, sfk=1112)),
    ("D3 S3, PFK 669 + SFK 1.112 (ikisi kötü)", dict(Pb=20, E=40, pfk=669, sfk=1112)),
    ("D4 S3, kur 62", dict(Pb=20, E=40, kur=62)),
]
out = []
print(f"{'Senaryo':<50}{'Yatırım':>8}{'PFK':>7}{'BatSFK':>7}{'SntSFK':>7}{'Al-sat':>7}{'SntEnj':>8}{'Net':>7}{'Geri':>6}{'IRR%':>7}{'NPV':>7}")
for ad, kw in S:
    r = coz(**kw); r["senaryo"] = ad; out.append(r)
    print(f"{ad:<50}{r['capex']:>8}{r['pfk_gelir']:>7}{r['bat_sfk_gelir']:>7}{r['santral_sfk_gelir']:>7}{r['alsat']:>7}{r['santral_enerji_degisim']:>8}{r['net']:>7}{str(r['geri_odeme']):>6}{str(r.get('irr','-')):>7}{r['npv']:>7.0f}", flush=True)
json.dump(out, open("portfoy_sonuclari.json", "w"), ensure_ascii=False, indent=1)
