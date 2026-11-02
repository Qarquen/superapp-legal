"""Çok basit, tek sayfalık özet tablo (v2). Python optimizasyonundan gelen değerler girdi olarak, geri kalan her şey formül."""
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

OUT = "/home/user/superapp-legal/bess-20mw/BESS_Basit_Tablo_v2.xlsx"
R = {x["senaryo"][:2].strip(): x for x in json.load(open("optimizasyon_sonuclari.json", encoding="utf-8"))}

wb = openpyxl.Workbook(); ws = wb.active; ws.title = "Özet"
ws.sheet_view.showGridLines = False
for col, w in zip("ABCDEFGHIJK", [40, 11, 11, 13, 11, 13, 12, 12, 12, 12, 12]):
    ws.column_dimensions[col].width = w

A = "Arial"
BLUE = Font(name=A, size=11, color="0000FF"); BLACK = Font(name=A, size=11); BOLD = Font(name=A, size=11, bold=True)
ORANGE = Font(name=A, size=11, color="C55A11", bold=True); GRAY = Font(name=A, size=10, italic=True, color="595959")
HDR = Font(name=A, size=10, bold=True, color="FFFFFF"); SECT = Font(name=A, size=12, bold=True, color="1F4E79")
TITLE = Font(name=A, size=15, bold=True)
YEL = PatternFill("solid", fgColor="FFFF00"); GRN = PatternFill("solid", fgColor="E2EFDA"); RED = PatternFill("solid", fgColor="FCE4D6")
ORF = PatternFill("solid", fgColor="FBE5D6"); HF = PatternFill("solid", fgColor="1F4E79")
thin = Side(style="thin", color="BFBFBF"); BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
N0, N1, N2 = '#,##0', '#,##0.0', '0.00'


def c(addr, v, font=BLACK, fmt=None, fill=None, box=True, wrap=False, center=False):
    x = ws[addr]; x.value = v; x.font = font
    if fmt: x.number_format = fmt
    if fill: x.fill = fill
    if box: x.border = BOX
    x.alignment = Alignment(wrap_text=wrap, vertical="center", horizontal="center" if center else None)
    return x


def hdr(row, labels, start="A"):
    for i, t in enumerate(labels):
        x = ws.cell(row=row, column=ord(start) - 64 + i, value=t)
        x.font = HDR; x.fill = HF; x.border = BOX
        x.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = 32


def note(row, text):
    ws.merge_cells(f"A{row}:K{row}"); c(f"A{row}", text, GRAY, box=False, wrap=True); ws.row_dimensions[row].height = 30


c("A1", "20 MW Batarya — Basit Analiz Tablosu (v2, 1 Kasım 2026)", TITLE, box=False)
note(2, "Mavi = değiştirebileceğin girdi · Turuncu = ÖRNEK değer, kendi verinle değiştir · Gri notlu sayılar Python analizinden (gerçek EPİAŞ saatlik fiyatları) · Siyah = formül")

# ---- 1) Ortak girdiler
c("A4", "1) ORTAK GİRDİLER", SECT, box=False)
inp = [(5, "Dolar kuru (TL/USD)", 43.5, N2, YEL, "Ocak 2026 değeri — güncelle"),
       (6, "Batarya enerji maliyeti (USD/kWh)", 95, N0, None, "Tahmin, teklif değil"),
       (7, "Batarya güç maliyeti (USD/kW)", 170, N0, None, "Tahmin, teklif değil"),
       (8, "SFK fiyatı (TL/MW-saat)", 2000, N0, YEL, "2026 gerçekleşen haftalar: 1.112 – 4.701"),
       (9, "SFK satılan saat (yıl)", 6500, N0, None, "İhale kazanma + kullanılabilirlik"),
       (10, "SFK teklif bloğu (saat)", 4, N0, YEL, "TEİAŞ blok süresi — teyit edilmeli (3/4/5 saat)"),
       (11, "Bakım gideri (yatırımın %’si)", 0.04, '0%', None, "Proje varsayımı"),
       (12, "Sistem + dengesizlik gideri (M TL/yıl)", 5, N1, None, "Tahmin, EPDK tarifesiyle netleşecek"),
       (13, "Santralin marjinal maliyeti (TL/MWh)", 1500, N0, None, "Santral PTF 1.500 altında yük düşürüyor")]
for r, lab, v, fmt, fill, nt in inp:
    c(f"A{r}", lab); c(f"B{r}", v, BLUE, fmt, fill)
    ws.merge_cells(f"C{r}:K{r}"); c(f"C{r}", nt, GRAY, box=False)

# ---- 2) Gerçek veri
c("A15", "2) GERÇEK FİYAT VERİSİ — EPİAŞ saatlik PTF, 25.04.2025–24.04.2026 (Python)", SECT, box=False)
veri = [(16, "Ortalama PTF (TL/MWh)", 2466, "Doğrulama: Temmuz 2025 ortalaması 2.965,16 — Montel ile birebir aynı"),
        (17, "Günlük spread, en pahalı 2 saat − en ucuz 2 saat (TL/MWh)", 2029, "Medyan 1.950 · sunumdaki 1.900 varsayımı doğrulandı"),
        (18, "2025’te PTF < 1.500 olan saat", 889, "Santral verisiyle birebir aynı (889)"),
        (19, "Santral marjı ortalaması, max(PTF − 1.500; 0) (TL/MWh)", 1128, "1 MW santral çıkışı kısılırsa kaybedilen ortalama kâr")]
for r, lab, v, nt in veri:
    c(f"A{r}", lab); c(f"B{r}", v, BLACK, N0)
    ws.merge_cells(f"C{r}:K{r}"); c(f"C{r}", nt, GRAY, box=False)

# ---- 3) SFK kuralı hesaplayıcı
c("A21", "3) SFK KURALI — batarya ne kadar SFK satabilir?", SECT, box=False)
c("A22", "Batarya gücü (MW)"); c("B22", 20, BLUE, N0, YEL)
c("A23", "Batarya enerjisi (MWh)"); c("B23", 40, BLUE, N0, YEL)
c("A24", "Satılabilecek en fazla SFK (MW)", BOLD); c("B24", "=MIN(B22,B23/(2.25*B10))", BOLD, N1, GRN)
c("A25", "10 MW kurulu güç şartı"); c("B25", '=IF(B22>=10,"UYGUN","GİREMEZ")', BOLD)
ws.merge_cells("C24:K25")
c("C24", "Kural: enerji ≥ rezerv × blok süresi × 2 yön × 1,125. 4 saatlik blokta 1 MW SFK için 9 MWh gerekir. Yani sınır çoğu zaman MW değil MWh’tir.", GRAY, box=False, wrap=True)

# ---- 4) Seçenekler
c("A27", "4) SEÇENEKLER — hangisi 5 yılın altında?", SECT, box=False)
hdr(28, ["Seçenek", "Güç (MW)", "Enerji (MWh)", "Yatırım (M TL)", "SFK (MW)", "SFK geliri (M TL)", "Al-sat (M TL)", "Gider (M TL)", "Net (M TL/yıl)", "Geri ödeme (yıl)", "5 yıl?"])
sec = [(29, "A · 20 MW / 40 MWh (eski sunum)", 20, 40, "A"), (30, "B · 20 MW / 90 MWh", 20, 90, "B"),
       (31, "C · 10 MW / 90 MWh", 10, 90, "C"), (32, "D · 20 MW / 180 MWh", 20, 180, "D")]
for r, lab, P, E, k in sec:
    c(f"A{r}", lab, BOLD if k in "CD" else BLACK)
    c(f"B{r}", P, BLUE, N0); c(f"C{r}", E, BLUE, N0)
    c(f"D{r}", f"=(C{r}*1000*$B$6+B{r}*1000*$B$7)*$B$5/1000000", BLACK, N1)
    c(f"E{r}", f"=MIN(B{r},C{r}/(2.25*$B$10))", BLACK, N1)
    c(f"F{r}", f"=E{r}*$B$9*$B$8/1000000", BLACK, N1)
    c(f"G{r}", R[k]["arb_net_mtl"], BLACK, N1)
    c(f"H{r}", f"=D{r}*$B$11+$B$12", BLACK, N1)
    c(f"I{r}", f"=F{r}+G{r}-H{r}", BOLD, N1)
    c(f"J{r}", f'=IF(I{r}<=0,"-",D{r}/I{r})', BOLD, N1, GRN if k in "CD" else None)
    c(f"K{r}", f'=IF(ISNUMBER(J{r}),IF(J{r}<=5,"EVET","HAYIR"),"HAYIR")', BOLD, center=True)
note(33, "Al-sat sütunu Python optimizasyonundan (gerçek saatlik fiyat, %85 yakalama, çevrim aşınması düşülmüş). SFK bedeli ödendiğinde enerji rezerve ayrıldığı için al-sat neredeyse sıfıra iner. "
         "Python sonuçları: A 7,6 · B 5,0 · C 4,2 · D 4,1 yıl (tablo ±%5 içinde aynı).")

# ---- 5) 20 MW üstü
c("A35", "5) 20 MW’IN ÜSTÜNE ÇIKMAK — santral çıkışını kısarak, ek her 1 MW SFK için", SECT, box=False)
ust = [(36, "Ek batarya yatırımı (M TL)", "=(2.25*$B$10*1000*$B$6+1000*$B$7)*$B$5/1000000", "1 MW güç + blok kuralının istediği enerji"),
       (37, "SFK geliri (M TL/yıl)", "=$B$9*$B$8/1000000", ""),
       (38, "Santralin kaybettiği kâr (M TL/yıl)", "=$B$19*$B$9/1000000", "Santral bu MW’ı satamaz: ortalama marj × SFK saati"),
       (39, "Bakım (M TL/yıl)", "=B36*$B$11", ""),
       (40, "Net (M TL/yıl)", "=B37-B38-B39", ""),
       (41, "Geri ödeme (yıl)", '=IF(B40<=0,"-",B36/B40)', "5 yılın çok üstünde → 20 MW’ın üstü bu fiyatlarla değmez")]
for r, lab, f, nt in ust:
    c(f"A{r}", lab, BOLD if r == 41 else BLACK); c(f"B{r}", f, BOLD if r == 41 else BLACK, N1, RED if r == 41 else None)
    ws.merge_cells(f"C{r}:K{r}"); c(f"C{r}", nt, GRAY, box=False)

# ---- 6) Santralin kendi SFK'sı
c("A43", "6) BATARYASIZ SEÇENEK — santralin kendi SFK teklifini 1 MW artırmak", SECT, box=False)
c("A44", "Yıllık ek kazanç (M TL/MW)", BOLD); c("B44", "=$B$9*($B$8-$B$19)/1000000", BOLD, N1, GRN)
c("A45", "Yatırım"); c("B45", 0, BLACK, N0)
ws.merge_cells("C44:K45")
c("C44", "SFK fiyatı (2.000) santralin kaybettiği ortalama kârdan (1.128) yüksek, yani santral kendi yedeğini artırırsa yatırımsız kazanır. "
          "DİKKAT: kısmi yükte verim kaybı ve rampa kabiliyeti dahil değil; santralin bugünkü SFK miktarını bilmiyoruz.", GRAY, box=False, wrap=True)

# ---- 7) Mevcut anlaşma
c("A47", "7) MEVCUT YAN HİZMET ANLAŞMASININ ETKİSİ — Seçenek C için (turuncular ÖRNEK)", SECT, box=False)
mev = [(48, "Yeni katılımcı olsaydık tek seferlik maliyet (M TL)", 10, "Test, SCADA/AGC bağlantısı, hukuk — ÖRNEK"),
       (49, "Mevcut anlaşmayla tek seferlik maliyet (M TL)", 3, "Batarya yine kendi performans testini geçmeli — ÖRNEK"),
       (50, "Gelire erken başlama (ay)", 3, "Anlaşma hazır olduğu için kazanılan süre — ÖRNEK")]
for r, lab, v, nt in mev:
    c(f"A{r}", lab); c(f"B{r}", v, ORANGE, N1, ORF)
    ws.merge_cells(f"C{r}:K{r}"); c(f"C{r}", nt, GRAY, box=False)
calc = [(51, "Tek seferlik tasarruf (M TL)", "=B48-B49"),
        (52, "Erken başlamanın kazandırdığı gelir (M TL)", "=F31/12*B50"),
        (53, "Toplam fayda (M TL)", "=B51+B52"),
        (54, "Seçenek C geri ödeme — anlaşmasız (yıl)", "=D31/I31"),
        (55, "Seçenek C geri ödeme — mevcut anlaşmayla (yıl)", "=(D31-B53)/I31")]
for r, lab, f in calc:
    c(f"A{r}", lab, BOLD if r in (53, 55) else BLACK); c(f"B{r}", f, BOLD if r in (53, 55) else BLACK, N2 if r >= 54 else N1, GRN if r == 55 else None)

# ---- 8) Duyarlılık
c("A57", "8) SFK FİYATI DEĞİŞİRSE — geri ödeme (yıl)", SECT, box=False)
hdr(58, ["SFK fiyatı (TL/MW-saat)", "C · 10/90", "D · 20/180", "Ne zaman görüldü"])
for i, (pr, nt) in enumerate([(844, "2025 ilk çeyrek (ikincil kaynak)"), (1112, "2026 en düşük hafta"), (2000, "Modeldeki değer"),
                               (3362, "2026, 18. hafta"), (4701, "2026 en yüksek hafta")]):
    r = 59 + i
    c(f"A{r}", pr, BLUE, N0, YEL)
    for col, row_ in (("B", 31), ("C", 32)):
        den = f"(E{row_}*$B$9*A{r}/1000000+G{row_}-H{row_})"
        c(f"{col}{r}", f'=IF({den}<=0,"-",D{row_}/{den})', BOLD, N1)
    ws.merge_cells(f"D{r}:K{r}"); c(f"D{r}", nt, GRAY, box=False)
note(64, "Kaynaklar: EPİAŞ saatlik PTF (github.com/oskkee/epias-ptf-data, yayınlanmış değerlerle doğrulandı) · SFK fiyatları: EPİAŞ haftalık raporları 2026 · "
         "SFK enerji kuralı: TEİAŞ depolama kriterleri (ikincil kaynak, resmî metinle teyit edilmeli) · Python kodu: bess-20mw/analiz/")
ws.page_setup.orientation = "landscape"; ws.sheet_properties.pageSetUpPr.fitToPage = True
ws.page_setup.fitToWidth = 1; ws.page_setup.fitToHeight = 0
wb.save(OUT); print("kaydedildi", OUT)
