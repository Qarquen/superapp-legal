"""Sade tek sayfa tablo (v3): kur 50, PFK + SFK seçenekleri, yan hizmet özeti."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

OUT = "/home/user/superapp-legal/bess-20mw/BESS_Sade_Tablo_v3.xlsx"
wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Özet"; ws.sheet_view.showGridLines = False
for col, w in zip("ABCDEFGHIJKL", [34, 9, 9, 9, 12, 10, 12, 10, 11, 11, 8, 13]):
    ws.column_dimensions[col].width = w
A = "Arial"
BLUE = Font(name=A, size=11, color="0000FF"); BLK = Font(name=A, size=11); BOLD = Font(name=A, size=11, bold=True)
GRAY = Font(name=A, size=10, italic=True, color="595959"); HDR = Font(name=A, size=10, bold=True, color="FFFFFF")
SECT = Font(name=A, size=12, bold=True, color="1F4E79"); TITLE = Font(name=A, size=15, bold=True)
YEL = PatternFill("solid", fgColor="FFFF00"); GRN = PatternFill("solid", fgColor="E2EFDA"); RED = PatternFill("solid", fgColor="FCE4D6")
HF = PatternFill("solid", fgColor="1F4E79"); thin = Side(style="thin", color="BFBFBF"); BOX = Border(top=thin, bottom=thin, left=thin, right=thin)


def c(a, v, f=BLK, fmt=None, fill=None, box=True, wrap=False):
    x = ws[a]; x.value = v; x.font = f; x.border = BOX if box else Border()
    if fmt: x.number_format = fmt
    if fill: x.fill = fill
    x.alignment = Alignment(wrap_text=wrap, vertical="center")


def hdr(row, labels):
    for i, t in enumerate(labels):
        x = ws.cell(row=row, column=1 + i, value=t); x.font = HDR; x.fill = HF; x.border = BOX
        x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 34


def note(row, text, h=30):
    ws.merge_cells(f"A{row}:L{row}"); c(f"A{row}", text, GRAY, box=False, wrap=True); ws.row_dimensions[row].height = h


c("A1", "20 MW Batarya — Sade Tablo (kur 50 TL/USD)", TITLE, box=False)
note(2, "Mavi = değiştirebilirsin · Sarı = en önemli girdiler · Siyah = formül. Fiyatlar TL olarak sabit tutuldu (kur artarken fiyatların da artacağı varsayılmadı).", 22)

c("A4", "1) GİRDİLER", SECT, box=False)
G = [(5, "Dolar kuru (TL/USD)", 50, '0.00', YEL, "Kullanıcının verdiği güncel kur"),
     (6, "Batarya enerji maliyeti (USD/kWh)", 95, '0', None, "Tahmin, teklif değil"),
     (7, "Batarya güç maliyeti (USD/kW)", 170, '0', None, "Tahmin, teklif değil"),
     (8, "PFK fiyatı (TL/MW-saat)", 1879, '#,##0', YEL, "ZAYIF KAYNAK: 2026 ilk çeyrek ortalaması, blog yazısı. 2025 ilk çeyrek: 669"),
     (9, "SFK fiyatı (TL/MW-saat)", 2000, '#,##0', YEL, "EPİAŞ 2026 haftalık: 1.112 – 4.701; burada temkinli değer"),
     (10, "Hizmet satılan saat (yıl)", 6500, '#,##0', None, "İhale kazanma + kullanılabilirlik"),
     (11, "Bakım gideri (yatırımın %’si)", 0.04, '0%', None, ""),
     (12, "Sistem + dengesizlik gideri (M TL/yıl)", 5, '0.0', None, "Tahmin")]
for r, lab, v, fmt, fill, nt in G:
    c(f"A{r}", lab); c(f"B{r}", v, BLUE, fmt, fill)
    ws.merge_cells(f"C{r}:L{r}"); c(f"C{r}", nt, GRAY, box=False)

c("A14", "2) SEÇENEKLER", SECT, box=False)
hdr(15, ["Seçenek", "Hizmet", "Güç (MW)", "Enerji (MWh)", "Yatırım (M TL)", "Satılan (MW)", "Yıllık gelir (M TL)", "Gider (M TL)", "Net (M TL/yıl)", "Geri ödeme (yıl)", "5 yıl?", "5 yıl için gereken fiyat"])
S = [(16, "1 · Primer frekans", "PFK", 20, 40, 1.25, "$B$8"),
     (17, "2 · Sekonder frekans, küçük", "SFK", 10, 90, 9, "$B$9"),
     (18, "3 · Sekonder frekans, büyük", "SFK", 20, 180, 9, "$B$9"),
     (19, "4 · Eski sunum (SFK, 20/40)", "SFK", 20, 40, 9, "$B$9")]
for r, lab, hz, P, E, oran, fiyat in S:
    c(f"A{r}", lab, BOLD if r == 16 else BLK); c(f"B{r}", hz)
    c(f"C{r}", P, BLUE, '0'); c(f"D{r}", E, BLUE, '0')
    c(f"E{r}", f"=(D{r}*1000*$B$6+C{r}*1000*$B$7)*$B$5/1000000", BLK, '#,##0.0')
    c(f"F{r}", f"=MIN(C{r},D{r}/{oran})", BLK, '0.0')
    c(f"G{r}", f"=F{r}*$B$10*{fiyat}/1000000", BLK, '#,##0.0')
    c(f"H{r}", f"=E{r}*$B$11+$B$12", BLK, '#,##0.0')
    c(f"I{r}", f"=G{r}-H{r}", BOLD, '#,##0.0')
    c(f"J{r}", f'=IF(I{r}<=0,"-",E{r}/I{r})', BOLD, '0.0', GRN if r != 19 else RED)
    c(f"K{r}", f'=IF(ISNUMBER(J{r}),IF(J{r}<=5,"EVET","HAYIR"),"HAYIR")', BOLD)
    c(f"L{r}", f"=(E{r}/5+H{r})*1000000/(F{r}*$B$10)", BLK, '#,##0')
note(20, "Satılan MW = en küçük(güç ; enerji ÷ oran). Oran PFK’da 1,25, SFK’da (4 saatlik blok) 9. "
         "Al-sat geliri eklenmedi: hizmet satılırken enerji yedekte durduğu için küçük kalıyor (Python’da 0–3 M TL). Python sonuçları: 1,6 · 4,9 · 4,8 · 9,2 yıl.", 32)

c("A22", "3) TÜM YAN HİZMETLER — bizim için ne ifade ediyor?", SECT, box=False)
hdr(23, ["Hizmet", "Ne ödüyor?", "", "", "Batarya kuralı", "", "", "Bizim için", "", "", "", ""])
for a, b in (("B23", "D23"), ("E23", "G23"), ("H23", "L23")): ws.merge_cells(f"{a}:{b}")
Y = [(24, "Primer frekans (PFK)", "Saatlik kapasite bedeli, TL/MW", "Enerji ≥ 1,25 × MW; 2 sn içinde tepki", "EN İYİ SEÇENEK — 20/40 ile 20 MW satılır. Fiyat verisi zayıf, pazar küçük: teyit şart"),
     (25, "Sekonder frekans (SFK)", "Saatlik kapasite bedeli, TL/MW", "Enerji ≥ 9 × MW (4 saatlik blok); en az 10 MW", "Yapılır ama pahalı: 9 kat enerji gerekiyor. Santral zaten SFK veriyor"),
     (26, "Dengeleme piyasası (YAL/YAT)", "Talimat başına enerji, SMF fiyatıyla", "Kapasite bedeli yok; talimat gelirse", "Ek gelir olabilir; SMF serisi elimizde yok, hesaba katılmadı"),
     (27, "Reaktif güç kontrolü", "Sözleşme dahilinde zorunlu; ödeme sınırlı", "Batarya inverteri yapabilir", "Gelir yok sayıldı; santralin yükümlülüğüne destek"),
     (28, "Oturan sistemin toparlanması", "Ayrı anlaşmayla; formül bulunamadı", "Batarya buna uygun", "Pazarlık konusu; hesaba katılmadı"),
     (29, "Talep tarafı katılımı", "Tüketiciler için", "—", "Bize uygun değil")]
for r, a_, b_, e_, h_ in Y:
    c(f"A{r}", a_, BOLD if r == 24 else BLK)
    for a, b, v in (("B", "D", b_), ("E", "G", e_), ("H", "L", h_)):
        ws.merge_cells(f"{a}{r}:{b}{r}"); c(f"{a}{r}", v, BLK, wrap=True, fill=GRN if r == 24 and a == "H" else None)
    ws.row_dimensions[r].height = 32

c("A31", "4) BATARYASIZ FIRSAT", SECT, box=False)
c("A32", "Santralin ortalama marjı (TL/MWh)"); c("B32", 1128, BLUE, '#,##0')
ws.merge_cells("C32:L32"); c("C32", "Gerçek veri: max(PTF − 1.500; 0), son 12 ay", GRAY, box=False)
c("A33", "Santral kendi SFK’sını 1 MW artırırsa (M TL/yıl)", BOLD); c("B33", "=$B$10*($B$9-B32)/1000000", BOLD, '0.0', GRN)
ws.merge_cells("C33:L33"); c("C33", "Yatırımsız. Kısmi yük verim kaybı ve rampa kabiliyeti dahil değil.", GRAY, box=False)

ORN = Font(name=A, size=11, color="C55A11", bold=True); ORF = PatternFill("solid", fgColor="FBE5D6")
c("A35", "5) ÖNERİLEN KURGU — santral sekonder, batarya primer", SECT, box=False)
K = [(36, "Santral sekonder geliri (M TL/yıl)", 382.0, BLK, '#,##0.0', None, "Python portföy optimizasyonu: 250–350 MW aralığında en fazla ±50 MW"),
     (37, "Santralin kaybettiği elektrik satışı (M TL/yıl)", 252.9, BLK, '#,##0.0', None, "Aşağı yedek için santral 300 MW üstünde kalmalı — ucuz saatlerde zararına üretim"),
     (38, "Santral sekonder NETİ (M TL/yıl)", "=B36-B37", BOLD, '#,##0.0', None, "Yatırımsız; verim kaybı ve aşınma dahil değil"),
     (39, "Batarya primer neti (M TL/yıl)", "=I16", BOLD, '#,##0.0', None, "Seçenek 1"),
     (40, "TOPLAM (M TL/yıl)", "=B38+B39", BOLD, '#,##0.0', GRN, "")]
for r, lab, v, f, fmt, fill, nt in K:
    c(f"A{r}", lab, BOLD if r == 40 else BLK); c(f"B{r}", v, f, fmt, fill)
    ws.merge_cells(f"C{r}:L{r}"); c(f"C{r}", nt, GRAY, box=False)

c("A42", "6) SEÇENEK 1 DUYARLILIK — geri ödeme (yıl)", SECT, box=False)
for i, (pr, nt) in enumerate([(669, "PFK 2025 ilk çeyrek seviyesi"), (1879, "Modeldeki değer"), (3000, "Yüksek")]):
    r = 43 + i
    c(f"A{r}", f"PFK fiyatı {pr:,} TL/MW-saat".replace(",", ".")); c(f"C{r}", pr, BLUE, '#,##0')
    c(f"B{r}", f"=E16/(F16*$B$10*C{r}/1000000-H16)", BOLD, '0.0')
    ws.merge_cells(f"D{r}:L{r}"); c(f"D{r}", nt, GRAY, box=False)
c("A46", "Kur 62 TL/USD olursa"); c("C46", 62, BLUE, '0')
c("B46", "=((D16*1000*$B$6+C16*1000*$B$7)*C46/1000000)/(G16-((D16*1000*$B$6+C16*1000*$B$7)*C46/1000000*$B$11+$B$12))", BOLD, '0.0')
ws.merge_cells("D46:L46"); c("D46", "TL fiyatlar sabit", GRAY, box=False)

c("A48", "7) TEŞVİK DEĞERLERİ — Seçenek 1", SECT, box=False)
c("A49", "Gümrük muafiyetinin değeri (M TL)"); c("B49", "=D16*1000*$B$6*0.3*$B$5/1000000", BOLD, '#,##0.0')
ws.merge_cells("C49:L49"); c("C49", "Batarya tarafı × %30 ilave gümrük vergisi (tamamının vergiye girdiği varsayımıyla)", GRAY, box=False)
c("A50", "KDV istisnası (M TL, nakit akışı)"); c("B50", "=E16*0.2", BOLD, '#,##0.0')
ws.merge_cells("C50:L50"); c("C50", "KDV indirilebilir; kalıcı kazanç değil", GRAY, box=False)

note(52, "Veri: EPİAŞ saatlik PTF 25.04.2025–24.04.2026 (Temmuz 2025 ortalaması 2.965,16 ve 2025’te 889 saat PTF<1.500 ile doğrulandı). "
         "Kurallar ikincil kaynaklardan (TEİAŞ depolama kriterleri) — resmî metinle teyit edilmeli. Birim maliyetler teklif değil.", 32)

import json as _j
P = {x["senaryo"][:3].strip(): x for x in _j.load(open("/home/user/superapp-legal/bess-20mw/analiz/portfoy_sonuclari.json", encoding="utf-8"))}
w2 = wb.create_sheet("Senaryolar"); w2.sheet_view.showGridLines = False
for col, wd in zip("ABCDEFGHI", [46, 11, 11, 11, 12, 12, 13, 13, 12]): w2.column_dimensions[col].width = wd
def c2(a, v, f=BLK, fmt=None, fill=None, wrap=False):
    x = w2[a]; x.value = v; x.font = f; x.border = BOX
    if fmt: x.number_format = fmt
    if fill: x.fill = fill
    x.alignment = Alignment(wrap_text=wrap, vertical="center")
w2["A1"].value = "Python portföy optimizasyonu — santral + batarya, 8.760 saat, gerçek EPİAŞ fiyatları"; w2["A1"].font = TITLE
w2["A2"].value = "Gri sayılar Python sonucu (portfoy_optimizasyon.py), siyah sütunlar formül. Bataryanın katkısı = senaryo neti − bataryasız referans."; w2["A2"].font = GRAY
H = ["Senaryo", "Yatırım (M TL)", "Primer (M TL)", "Santral sek. (M TL)", "Santral enerji kaybı", "Portföy net (M TL/yıl)", "Referans net (bataryasız)", "Bataryanın katkısı", "Batarya geri ödeme (yıl)"]
for i, t in enumerate(H):
    x = w2.cell(row=4, column=1 + i, value=t); x.font = HDR; x.fill = HF; x.border = BOX
    x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
w2.row_dimensions[4].height = 44
rows = [("S1", "S1 — Yalnız santral sekonder (bataryasız)", None), ("S3", "Önerilen: batarya 20/40 + santral sekonder", "S1"),
        ("S4", "Ucuz enerji: batarya 20/25 + santral sekonder", "S1"), ("S5", "Büyük: batarya 40/50 + santral sekonder", "S1"),
        ("S6", "Daha büyük: batarya 50/63 + santral sekonder", "S1"), ("S7", "Primer pazarı 10 MW ile sınırlı", "S1"),
        ("D1", "Primer 669 (2025 seviyesi)", "S1"), ("D2", "Sekonder 1.112 (2026 en düşük)", "S1b"),
        ("D3", "Primer 669 + sekonder 1.112 (ikisi kötü)", "S1b"), ("D4", "Kur 62", "S1")]
GF = Font(name=A, size=11, color="595959")
for i, (k, lab, ref) in enumerate(rows):
    r = 5 + i; x = P[k]
    c2(f"A{r}", lab, BOLD if k == "S3" else BLK)
    c2(f"B{r}", x["capex"], GF, '#,##0.0'); c2(f"C{r}", x["pfk_gelir"], GF, '#,##0.0')
    c2(f"D{r}", x["santral_sfk_gelir"], GF, '#,##0.0'); c2(f"E{r}", x["santral_enerji_degisim"], GF, '#,##0.0')
    c2(f"F{r}", x["net"], GF, '#,##0.0'); c2(f"G{r}", P[ref]["net"] if ref else 0, GF, '#,##0.0')
    if ref:
        c2(f"H{r}", f"=F{r}-G{r}", BOLD, '#,##0.0')
        c2(f"I{r}", f'=IF(H{r}<=0,"-",B{r}/H{r})', BOLD, '0.0', GRN if k == "S3" else None)
    else:
        c2(f"H{r}", "—"); c2(f"I{r}", "yatırımsız")
r = 5 + len(rows) + 1
w2[f"A{r}"].value = "20 MW üstü — ek batarya MW’larının kendi geri ödemesi"; w2[f"A{r}"].font = SECT
for j, (k, lab) in enumerate([("S5", "40/50’ye çıkmak (S5 − S3)"), ("S6", "50/63’e çıkmak (S6 − S3)")]):
    rr = r + 1 + j; i5 = 5 + [q[0] for q in rows].index(k)
    c2(f"A{rr}", lab); c2(f"B{rr}", f"=B{i5}-B6", BLK, '#,##0.0'); c2(f"F{rr}", f"=F{i5}-F6", BLK, '#,##0.0')
    c2(f"I{rr}", f"=B{rr}/F{rr}", BOLD, '0.0', RED)
w2[f"A{r+4}"].value = "Sonuç: 20 MW’ın üstündeki her MW, 370 MW sınırında santralin sekonder payını yerinden ediyor; ek yatırım 5 yılın üstünde dönüyor."
w2[f"A{r+4}"].font = GRAY
ws.page_setup.orientation = "landscape"; ws.sheet_properties.pageSetUpPr.fitToPage = True; ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
wb.save(OUT); print("kaydedildi")
