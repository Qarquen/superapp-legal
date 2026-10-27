# 20 MW Batarya Enerji Depolama (BESS) — İzdemir Enerji / Aliağa

Santralde boşta duran **20 MW bağlantı kapasitesinin** batarya depolamaya çevrilmesi için
fizibilite ve teşvik analizi. Hedef: **5 yılın altında amortisman.**

- Model: `Izdemir_BESS_20MW_Model.xlsx` (377 formül, 0 hata; LibreOffice ile recalc edildi)
- Sunum: Claude Slides deck (15 slayt)
- Tarih: 27 Ekim 2026

## Sonuç

| Kalem | Değer |
|---|---|
| Konfigürasyon | 20 MW / 40 MWh (2 saat), LFP, 34,5 kV bağlantı |
| CAPEX | 7,2 milyon USD = 313,2 milyon TL (180 USD/kWh, 360 USD/kW) |
| Brüt yıllık gelir | 140,2 milyon TL (SFK 130,0 + arbitraj 10,2) |
| İşletme gideri | −17,5 milyon TL (bakım 12,5 + sistem/dengesizlik 5,0) |
| Net yıllık nakit | 122,7 milyon TL = 2,82 milyon USD |
| **Basit geri ödeme** | **2,56 yıl** (iskontolu %10 → 3,10 yıl) |
| NPV (15 yıl, %10) | 605 milyon TL |
| IRR | %38,6 |

**5 yıl hedefi tutuyor — ama tek kaleme bağlı.** Gelirin **%93'ü** sekonder frekans kontrol (SFK)
kapasite bedelinden geliyor, arbitrajdan yalnızca %7.

### Kırılma noktası
5 yılda geri ödeme için gereken asgari SFK fiyatı: **1.077 TL/MW-h**
(arbitraj geliri hiç olmazsa 1.233 TL/MW-h).
2026'da gözlenen en düşük hafta 1.112 TL/MW — eşiğin hemen üzerinde.
2025 ilk çeyrek seviyesinde (~844 TL/MW) **hedef tutmuyor** (geri ödeme 18,3 yıl).

### Senaryolar
| | Kötü | Baz | İyi |
|---|---|---|---|
| SFK fiyatı (TL/MW-h) | 900 | 2.000 | 3.000 |
| Spread (TL/MWh) | 1.200 | 1.900 | 2.600 |
| CAPEX çarpanı | 1,25 | 1,00 | 0,85 |
| Geri ödeme | 18,3 yıl | 2,6 yıl | 1,1 yıl |

### Süre seçimi
| | 1 saat | 2 saat | 4 saat |
|---|---|---|---|
| CAPEX | 5,3 M USD | 7,2 M USD | 11,0 M USD |
| Birim | 265 USD/kWh | 180 USD/kWh | 137 USD/kWh |
| Geri ödeme | 1,9 yıl | **2,6 yıl** | 3,8 yıl |

SFK bedeli MW başına ödendiği için kısa süre daha hızlı geri öder; ancak 1 saat rezervi
taşımaya yetmez. **2 saat önerilir.**

### Kur duyarlılığı (TL gelirler sabit — muhafazakâr)
43,5 → 2,6 yıl · 48 → 2,9 yıl · 55 → 3,3 yıl · 62 → 3,8 yıl

## Teşvikler

| Destek | Durum | Etki |
|---|---|---|
| Gümrük vergisi muafiyeti (YTB) | VAR | 49,6 milyon TL'ye kadar gerçek tasarruf |
| KDV istisnası (YTB) | VAR | 62,6 milyon TL — indirilebilir, kalıcı kâr değil, nakit akışı |
| Vergi indirimi | **YOK** | Elektrik enerjisi depolama yatırımları yararlanamıyor |
| Faiz / kâr payı desteği | **YOK** | Elektrik üretim/dağıtım/depolama hariç tutulmuş |
| Sigorta primi işveren hissesi | ŞÜPHELİ | 1. bölgede destek yok; İzmir bölge/ilçe durumu teyit edilmeli |
| Yatırım yeri tahsisi | **YOK** | Elektrik üretimine tahsis yapılmıyor |
| Asgari yatırım eşiği (İzmir 12 M TL) | SAĞLANIYOR | Yatırım 313 M TL |

**Teşvik CAPEX'i ~%15 kırpar, kârı yaratmaz.** Devlet faiz desteği kapalı olduğundan finansman
kaldıracı TSKB / Dünya Bankası hatları (depolamalı projelerde 7–11 yıl vade, 1 yıl ödemesiz örnekleri).

### ACİL: gümrük penceresi 31.12.2026'da kapanıyor
11508 sayılı Cumhurbaşkanı Kararı (RG 11.07.2026) ile LFP batarya **hücresinde**
(GTİP 8507.60.00.00.21, ≤4,9 V) ilave gümrük vergisi 31.12.2026'ya kadar %0.
Paket/komple sistemlerde **%30** sürüyor → tedarik hücre bazlı kurgulanmazsa **+49,6 milyon TL**.
YTB ithalattan **önce** alınmalı.

## Lisans yolu

Mevcut üretim lisansına depolama ünitesi eklenmesi **lisans tadiliyle** yapılıyor; şartlar:
1. Saha sınırı dışına çıkılmaması — sağlanıyor
2. Lisanstaki kurulu gücün değişmemesi — sağlanıyor (350 MW sabit)
3. Bağlantı şekli, noktası ve gerilim seviyesinin aynı kalması — sağlanıyor (34,5 kV)

Ön lisans ve yarışma gerekmiyor (33,1 GW'lık depolamalı üretim ön lisans kuyruğuna girilmiyor).

**Dikkat:** "depolama gücü kadar kapasite artışı" hakkı yalnızca RES/GES üretim lisansı
sahiplerine tanınmış — termik lisansa bağlı 20 MW GES hakkı **doğmuyor**.

## Modelin muhafazakâr olduğu yerler

1. Santral entegrasyon değeri (yük düşürmeden kaçınma + dengesizlik azaltımı) **sıfır** alındı
   — yakıt marjinal maliyeti ve KGÜP sapma kaydı olmadan hesaplanamaz.
2. Kur yükselirken TL gelirler sabit tutuldu (gerçekte PTF/SFK kurla korele).
3. SFK fiyatı 2.000 TL/MW-h — 2026 gözlemlerinin (1.112–4.701) belirgin altında.

## Doğrulama

- `recalc.py`: 377 formül, **0 hata**.
- Bağımsız Python karşı denetimi: CAPEX, SFK geliri, deşarj/şarj enerjisi, net arbitraj,
  net yıllık nakit, geri ödeme, NPV ve eşik SFK fiyatı — **hepsi birebir eşleşti**.
- Yakalanan hata: "arbitraj gücü" formülü yanlış satıra referans veriyordu (20 MW yerine
  10 MW olmalı); düzeltildi ve yeniden doğrulandı.

## Kaynaklar ve güvenilirlik

Sınıflandırma: ölçülmüş santral verisi > teklif > kurum/literatür > basın > varsayım.

- **Santral verisi:** 350 MW ithal kömürlü, Aliağa; boşta 20 MW; 2025'te PTF < 1.500 TL/MWh
  olan 889 saat; 1 MW GES.
- **EPİAŞ Haftalık Raporları 2026** (5./8./9./18. hafta) — SFK ağırlıklı ortalama birim fiyat
  1.112 / 4.701 / 3.653 / 3.362 TL/MW; haftalık tedarik ~158–161 bin MW (≈955 MW/saat).
- **EPİAŞ günlük bültenleri** — 08.08.2026: gündüz 1.832,81 / puant 3.789,61 / gece 3.372,33,
  min 925,01 (12:00), max 4.059,02 (20:00); 20.05.2026: gündüz 197,17 / puant 2.564,40.
- **9903 sayılı Karar** (RG 30.05.2025) — teşvik kalemleri (ikincil özetler üzerinden).
- **11508 sayılı CB Kararı** (RG 11.07.2026) — LFP hücre İGV %0 penceresi.
- **Elektrik Piyasası Lisans Yönetmeliği** — depolama ünitesi tadil şartları.
- **Ember / Rystad / Modo Energy** — CAPEX kıyası (125 / 148–215 / 201 USD/kWh).
- **TSKB** — depolamalı proje finansman örnekleri.

> Birim maliyetler (95 USD/kWh, 170 USD/kW), RTE %88, 300 döngü, 6.500 SFK saati, sistem
> kullanım payı 5 M TL/yıl ve kur 43,50 TL/USD **VARSAYIMDIR, teklif değildir.**
> Mevzuat dayanakları ikincil kaynak özetlerinden alınmıştır; Resmî Gazete tam metinleri,
> mali müşavir ve gümrük müşaviri teyidi şarttır.

## Yapılacaklar (90 gün)

- **0–30 gün:** YTB başvurusu, gümrük müşavirinden GTİP yazısı, 3 EPC teklifi, EPDK/TEİAŞ yazılı görüş
- **30–60 gün:** lisans tadil dosyası, yan hizmet birimi belgelendirmesi, TSKB ön görüşme,
  modelin gerçek PTF/SFK serisiyle güncellenmesi
- **60–90 gün:** yatırım kararı, hücre siparişi (gümrük penceresi), EPC sözleşmesi + kapasite garantisi
