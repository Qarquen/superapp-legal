"""Proje durum özeti (kısa ama detaylı): durum, iyileştirme yolları, riskler, kaynaklar.
Model çıktıları (gri) bess_analiz.coz() sonuçlarıdır; siyah hücreler formüldür, mavi hücreler girdidir."""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

OUT = "/home/user/superapp-legal/bess-20mw/BESS_Durum_Ozeti.xlsx"
A = "Arial"
BLUE = Font(name=A, size=10, color="0000FF"); BLK = Font(name=A, size=10); BOLD = Font(name=A, size=10, bold=True)
GRAYF = Font(name=A, size=10, color="595959"); NOTE = Font(name=A, size=9, italic=True, color="595959")
HDR = Font(name=A, size=10, bold=True, color="FFFFFF"); SECT = Font(name=A, size=12, bold=True, color="1F4E79")
TITLE = Font(name=A, size=15, bold=True)
HF = PatternFill("solid", fgColor="1F4E79"); YEL = PatternFill("solid", fgColor="FFFF00")
OK = PatternFill("solid", fgColor="E2EFDA"); WARN = PatternFill("solid", fgColor="FFF2CC"); BAD = PatternFill("solid", fgColor="FCE4D6")
thin = Side(style="thin", color="BFBFBF"); BOX = Border(top=thin, bottom=thin, left=thin, right=thin)
DURUM_RENK = {"Tamam": OK, "Devam": WARN, "Bekliyor": BAD}

wb = openpyxl.Workbook()


def sheet(name, widths):
    ws = wb.active if wb.active.title == "Sheet" else wb.create_sheet()
    ws.title = name; ws.sheet_view.showGridLines = False
    for i, w in enumerate(widths):
        ws.column_dimensions[chr(65 + i)].width = w
    return ws


def put(ws, ref, v, f=BLK, fmt=None, fill=None, wrap=True, box=True, align=None):
    c = ws[ref]; c.value = v; c.font = f
    if fmt: c.number_format = fmt
    if fill: c.fill = fill
    if box: c.border = BOX
    c.alignment = Alignment(wrap_text=wrap, vertical="center", horizontal=align)
    return c


def header(ws, row, labels, h=30):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=1 + i, value=t); c.font = HDR; c.fill = HF; c.border = BOX
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[row].height = h


# ---------------------------------------------------------------- 1) DURUM
ws = sheet("Durum", [38, 15, 15, 15, 46])
put(ws, "A1", "İzdemir Aliağa — 20 MW / 40 MWh batarya: proje durumu", TITLE, box=False, wrap=False)
put(ws, "A2", "Mavi: girdi · Gri: Python modeli çıktısı · Siyah: formül · Tutarlar milyon TL, kur 50 TL/USD", NOTE, box=False, wrap=False)

put(ws, "A4", "1) PROJE TANIMI", SECT, box=False, wrap=False)
tanim = [("Batarya gücü (MW)", 20, "Primer frekans satar"), ("Batarya enerjisi (MWh)", 40, "8 × 5 MWh konteyner; ömür boyu 20 MW primer"),
         ("Santral sekonder bandı (MW)", 50, "250–350 MW çalışma aralığı; minimum yük düşerse büyür"),
         ("Bağlantı sınırı (MW)", 370, "Santral + batarya toplamı aşamaz"),
         ("Kur (TL/USD)", 50, ""), ("Enerji maliyeti (USD/kWh)", 95, "Tahmin; teklif yok"), ("Güç maliyeti (USD/kW)", 170, "Tahmin; teklif yok")]
for i, (k, v, n) in enumerate(tanim):
    r = 5 + i
    put(ws, f"A{r}", k); put(ws, f"B{r}", v, BLUE, '#,##0'); ws.merge_cells(f"C{r}:E{r}"); put(ws, f"C{r}", n, NOTE)
put(ws, "A12", "Yatırım (M TL)", BOLD); put(ws, "B12", "=(B6*1000*B10+B5*1000*B11)*B9/1000000", BOLD, '#,##0.0', YEL)
ws.merge_cells("C12:E12"); put(ws, "C12", "7,2 milyon USD", NOTE)

put(ws, "A14", "2) SONUÇ — üç fiyat seviyesi", SECT, box=False, wrap=False)
header(ws, 15, ["", "2025 ortalaması", "Ana senaryo (Oca–Mar 2026)", "Zirve haftalar (üst sınır)", "Not"])
put(ws, "A16", "Primer fiyatı (TL/MW-saat)"); put(ws, "B16", 1050, BLUE, '#,##0'); put(ws, "C16", 1879, BLUE, '#,##0'); put(ws, "D16", 4600, BLUE, '#,##0')
put(ws, "E16", "EPİAŞ aylık/haftalık raporları", NOTE)
put(ws, "A17", "Sekonder fiyatı (TL/MW-saat)"); put(ws, "B17", 1450, BLUE, '#,##0'); put(ws, "C17", 2000, BLUE, '#,##0'); put(ws, "D17", 3000, BLUE, '#,##0')
put(ws, "E17", "Zirve: yalnız birkaç hafta; yıl boyu sürmez", NOTE)
put(ws, "A18", "Bataryanın yıllık katkısı (net)"); put(ws, "B18", 122.2, GRAYF, '#,##0.0'); put(ws, "C18", 226.4, GRAYF, '#,##0.0'); put(ws, "D18", 578.6, GRAYF, '#,##0.0')
put(ws, "E18", "Bakım + sistem gideri düşülmüş", NOTE)
put(ws, "A19", "Santral sekonder neti (yatırımsız)"); put(ws, "B19", 52.7, GRAYF, '#,##0.0'); put(ws, "C19", 128.8, GRAYF, '#,##0.0'); put(ws, "D19", 409.8, GRAYF, '#,##0.0')
put(ws, "E19", "Kaybedilen elektrik satışı düşülmüş", NOTE)
put(ws, "A20", "Toplam yıllık ek kâr", BOLD)
for col in "BCD":
    put(ws, f"{col}20", f"={col}18+{col}19", BOLD, '#,##0.0')
put(ws, "A21", "Batarya geri ödeme (yıl)", BOLD)
for col in "BCD":
    put(ws, f"{col}21", f"=$B$12/{col}18", BOLD, '0.0', YEL if col == "C" else None)
put(ws, "E21", "Hedef: 5 yılın altı", NOTE)
put(ws, "A22", "5 yıl için gereken en düşük primer fiyatı"); put(ws, "C22", 562, GRAYF, '#,##0'); put(ws, "E22", "Altına kalıcı inerse batarya hedefi tutmaz", NOTE)

put(ws, "A24", "3) İŞ KALEMLERİ", SECT, box=False, wrap=False)
header(ws, 25, ["Konu", "Durum", "", "", "Sıradaki adım"])
isler = [("Fiyat verisi (PTF saatlik)", "Tamam", "EPİAŞ 8.760 saat, doğrulandı"),
         ("Primer/sekonder fiyat serisi", "Devam", "2025 kısmen var; Haz–Eki 2026 ve senin Excel’in bekleniyor"),
         ("Batarya boyu", "Tamam", "20 MW / 40 MWh netleşti"),
         ("Santral verisi (min. yük, sekonder bandı, primer yükümlülüğü)", "Bekliyor", "İşletmeden iste: en büyük kaldıraç"),
         ("Tedarikçi teklifleri", "Bekliyor", "3 firmadan 20 MW / 40 MWh anahtar teslim + garanti"),
         ("Lisans yolu (bütünleşik depolama)", "Devam", "EPDK’dan yazılı görüş; 19 Eki 2026 değişiklikleri okunmalı"),
         ("TEİAŞ kuralları (1,25 oranı)", "Devam", "Primer oranı EMO sunumuyla teyitli; resmî kriter metni okunmalı"),
         ("Teşvik belgesi (9903)", "Bekliyor", "Depolamanın kapsamda olduğu mali müşavirle teyit"),
         ("Finansman", "Bekliyor", "TSKB / yeşil kredi görüşmesi"),
         ("Sunum, Excel, Python modeli", "Tamam", "18 slayt; model gerçek veriyle çalışıyor")]
for i, (k, d, n) in enumerate(isler):
    r = 26 + i
    put(ws, f"A{r}", k); put(ws, f"B{r}", d, BOLD, fill=DURUM_RENK[d], align="center")
    ws.merge_cells(f"C{r}:E{r}"); put(ws, f"C{r}", n)
    ws.row_dimensions[r].height = 28
r = 26 + len(isler)
put(ws, f"A{r}", "Tamamlanan iş kalemi", BOLD); put(ws, f"B{r}", f'=COUNTIF(B26:B{r-1},"Tamam")&" / "&COUNTA(B26:B{r-1})', BOLD, align="center")

# ---------------------------------------------------------------- 2) İYİLEŞTİRME
w2 = sheet("İyileştirme", [34, 44, 12, 12, 12, 11, 11, 30])
put(w2, "A1", "Daha kârlı ve yapılabilir kılmak için yollar", TITLE, box=False, wrap=False)
put(w2, "A2", "Etkiler ana senaryo fiyatlarıyla (Oca–Mar 2026). Yeni geri ödeme = (yatırım + yatırım değişimi) ÷ (katkı + katkı değişimi).", NOTE, box=False, wrap=False)
put(w2, "A3", "Bugünkü yatırım (M TL)"); put(w2, "B3", "=Durum!B12", BOLD, '#,##0.0')
put(w2, "C3", "Katkı"); put(w2, "D3", "=Durum!C18", BOLD, '#,##0.0')
header(w2, 5, ["Yol", "Ne yapılır", "Yatırım değişimi (M TL)", "Yıllık katkı değişimi (M TL)", "Batarya geri ödeme (yıl)", "Zorluk", "Durum", "Kimden / ne lazım"], 44)
yollar = [
    ("1. Santral minimum yükünü 200 MW’a indirmek", "Sekonder bandı 50 → 75 MW. Batarya değil santral kazanır (yatırımsız).", 0, 64.4, "Orta", "Bekliyor", "Kazan üreticisi minimum yük onayı, düşük yük verimi"),
    ("2. Minimum yükü 150 MW’a indirmek", "Bant 100 MW. Düşük yükte verim kaybı ve aşınma ayrıca hesaplanmalı.", 0, 128.8, "Zor", "Bekliyor", "Santral teknik ekibi, TEİAŞ sekonder testi"),
    ("3. Rekabetçi ihale ile %20 ucuz batarya", "3+ teklif; piyasa ortalaması 117–125 USD/kWh, bizim tahmin ~180.", "=-0.2*B3", "=0.04*0.2*B3", "Kolay", "Bekliyor", "Tedarikçi teklifleri"),
    ("4. Santralin %5 primer yükümlülüğünü bataryaya devretmek", "350 MW × %5 = 17,5 MW. Santral o kapasiteyi satışa/sekondere açar.", 0, None, "Orta", "Bekliyor", "Santralin bugünkü primer anlaşması (rakam buna bağlı)"),
    ("5. Dengesizlik maliyetini batarya ile azaltmak", "Santral planından saparken batarya farkı kapatır.", 0, None, "Orta", "Bekliyor", "KGÜP ve dengesizlik kayıtları"),
    ("6. Esnek çalışma (primer düşerse sekonder/al-sat)", "EMS yazılımı her gün en kârlı hizmeti seçer; model bunu zaten yapıyor.", 0, 0, "Kolay", "Tamam", "Tasarımda EMS şartı"),
    ("7. Gümrük muafiyetini korumak (teşvik belgesi)", "Belge alınmazsa yatırım ~57 M TL artar.", 0, 0, "Kolay", "Bekliyor", "Mali müşavir, E-TUYS başvurusu"),
    ("8. Döviz kredisi ile kur riskini eşleştirmek", "Batarya dolar, gelir TL; USD kredi kur artışını dengeler.", 0, 0, "Orta", "Bekliyor", "TSKB / banka görüşmesi"),
]
for i, (y, n, dy, dk, z, d, kim) in enumerate(yollar):
    r = 6 + i
    put(w2, f"A{r}", y, BOLD); put(w2, f"B{r}", n)
    put(w2, f"C{r}", dy, BLUE if not isinstance(dy, str) else BLK, '#,##0.0')
    if dk is None:
        put(w2, f"D{r}", "veri lazım", NOTE, align="center"); put(w2, f"E{r}", "—", BLK, align="center")
    else:
        put(w2, f"D{r}", dk, GRAYF if not isinstance(dk, str) else BLK, '#,##0.0')
        santral_kazanci = y.startswith(("1.", "2."))   # santralin kazancı, bataryanın geri ödemesine girmez
        put(w2, f"E{r}", f"=($B$3+C{r})/$D$3" if santral_kazanci else f"=($B$3+C{r})/($D$3+D{r})", BOLD, '0.0')
    put(w2, f"F{r}", z, align="center"); put(w2, f"G{r}", d, BOLD, fill=DURUM_RENK[d], align="center"); put(w2, f"H{r}", kim, NOTE)
    w2.row_dimensions[r].height = 40
r = 6 + len(yollar) + 1
put(w2, f"A{r}", "1 ve 2 santralin kazancıdır, bataryanın geri ödemesini değiştirmez; toplam kâra eklenir.", NOTE, box=False, wrap=False)
put(w2, f"A{r+1}", "Toplam yıllık ek kâr, 3. yol + 1. yol ile (M TL)", BOLD)
put(w2, f"E{r+1}", "=Durum!C20+D6+D8", BOLD, '#,##0.0', YEL)

# ---------------------------------------------------------------- 3) RİSKLER
w3 = sheet("Riskler", [30, 10, 10, 46, 34])
put(w3, "A1", "Olası problemler ve çözümler", TITLE, box=False, wrap=False)
put(w3, "A2", "Olasılık / etki: Yüksek, Orta, Düşük", NOTE, box=False, wrap=False)
header(w3, 4, ["Problem", "Olasılık", "Etki", "Çözüm", "Takip göstergesi"])
riskler = [
    ("Yeni bataryalar primer fiyatını düşürür", "Yüksek", "Yüksek", "Hızlı geri ödeme (1,6 yıl); EMS ile sekonder/al-sata geçiş; erken devreye alma", "Aylık PFK fiyatı ve 560 TL eşiği; EPDK depolama lisansları"),
    ("Primer pazarı küçük (saatte ~270–420 MW)", "Orta", "Orta", "20 MW pazarın ~%5–7’si; daha büyük batarya yerine santral sekonderini büyüt", "TEİAŞ haftalık PFK miktarı"),
    ("Lisans yolu belirsiz (tadil mi, kurul kararı mı)", "Orta", "Yüksek", "Sipariş öncesi EPDK’dan yazılı görüş; enerji hukuku bürosu", "EPDK cevabı"),
    ("370 MW bağlantı sınırı aşılır", "Düşük", "Yüksek", "EMS’de santral + batarya güç sınırlayıcı; 19 Eki 2026 kuralı: otomatik kontrol ve kesme sistemi", "SCADA kayıtları"),
    ("TEİAŞ testi / sertifika gecikir", "Orta", "Orta", "Testi devreye almayla planla; sertifika uygulaması 31 Ara 2026’ya ertelendi", "TEİAŞ test takvimi"),
    ("Şarj enerjisinin tarifesi belirsiz", "Orta", "Düşük", "Primerde enerji çevrimi az; EPDK’dan tarife görüşü; modelde 5 M TL/yıl ayrıldı", "EPDK görüşü"),
    ("Batarya yaşlanır, 20 MW satılamaz", "Orta", "Orta", "40 MWh seçildi; tedarikçiden kapasite garantisi ve performans taahhüdü", "Yıllık kapasite testi"),
    ("Kur yükselir", "Orta", "Orta", "USD kredi; sipariş anında kur sabitleme. Kur 62’de geri ödeme 2,0 yıl", "TL/USD"),
    ("Teşvik belgesi alınamaz", "Düşük", "Orta", "Erken başvuru; alınmazsa yatırım ~57 M TL artar, geri ödeme ~1,8 yıl", "E-TUYS başvuru durumu"),
    ("Kömür sahasında yangın / sigorta", "Düşük", "Yüksek", "Konteynerler arası mesafe, söndürme sistemi, sigortacı onaylı tasarım", "Sigorta teklifi"),
    ("Santral lisansına bağımlılık", "Düşük", "Yüksek", "Batarya santral lisansına bağlı; santral durursa ne olacağı lisans görüşünde sorulmalı", "Hukuk görüşü"),
    ("Düşük yükte santral verimi düşer", "Orta", "Orta", "Minimum yük düşürmeden önce verim ve aşınma testi; modele eklenmeli", "Santral test raporu"),
]
for i, row in enumerate(riskler):
    r = 5 + i
    for j, v in enumerate(row):
        col = "ABCDE"[j]
        fill = None
        if j in (1, 2):
            fill = {"Yüksek": BAD, "Orta": WARN, "Düşük": OK}[v]
        put(w3, f"{col}{r}", v, BOLD if j == 0 else BLK, fill=fill, align="center" if j in (1, 2) else None)
    w3.row_dimensions[r].height = 40
r = 5 + len(riskler) + 1
put(w3, f"A{r}", "Yüksek olasılıklı risk sayısı", BOLD); put(w3, f"B{r}", f'=COUNTIF(B5:B{r-2},"Yüksek")', BOLD, '0', align="center")
put(w3, f"A{r+1}", "Yüksek etkili risk sayısı", BOLD); put(w3, f"B{r+1}", f'=COUNTIF(C5:C{r-2},"Yüksek")', BOLD, '0', align="center")

# ---------------------------------------------------------------- 4) KAYNAKLAR
w4 = sheet("Kaynaklar", [36, 90])
put(w4, "A1", "Kaynaklar", TITLE, box=False, wrap=False)
header(w4, 3, ["Konu", "Kaynak"])
kay = [("Saatlik PTF", "EPİAŞ Şeffaflık; github.com/oskkee/epias-ptf-data (25.04.2025–24.04.2026)"),
       ("PFK/SFK 2025 aylık", "EPİAŞ Elektrik Piyasaları Aylık Raporları (Ocak, Mart–Haziran, Aralık 2025)"),
       ("PFK/SFK 2026", "EPİAŞ Haftalık Raporları 2026 (2., 5., 8., 9., 11., 18. hafta)"),
       ("Depolama primer şartı 1,25", "TEİAŞ depolama kriterleri, EMO sunumu (emo.org.tr)"),
       ("Primer yükümlülüğü %5", "Elektrik Şebeke Yönetmeliği değişikliği (13.07.2023)"),
       ("Yükümlülük devri", "Elektrik Piyasası Yan Hizmetler Yönetmeliği"),
       ("Bütünleşik depolama, tek lisans", "Elektrik Piyasasında Depolama Faaliyetleri Yönetmeliği; Mondaq, Çakmak özetleri"),
       ("Lisans değişikliği", "Resmî Gazete 19.10.2026 (Lisans Yönetmeliği)"),
       ("Batarya maliyeti", "BNEF Aralık 2025 (117 USD/kWh), Ember Ekim 2025 (125 USD/kWh)"),
       ("Rakip bataryalar", "Göktepe BESS 108 MW/132 MWh, Haziran 2026 (Enerji Bülteni); EPDK 33,1 GW ön lisans (AA)"),
       ("Teşvik", "9903 sayılı Karar, RG 30.05.2025"),
       ("Model", "bess-20mw/analiz/bess_analiz.py (HiGHS doğrusal optimizasyon, 8.760 saat)")]
for i, (k, v) in enumerate(kay):
    put(w4, f"A{5 + i - 1}", k, BOLD); put(w4, f"B{5 + i - 1}", v)

for s in wb.worksheets:
    s.page_setup.orientation = "landscape"; s.sheet_properties.pageSetUpPr.fitToPage = True
    s.page_setup.fitToWidth = 1; s.page_setup.fitToHeight = 0
wb.save(OUT); print("kaydedildi", OUT)
