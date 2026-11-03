# Analizi kendin çalıştırmak

## En kolay yol: hazır defter (önerilen)
- **`BESS_Analiz.ipynb`**: tüm analizler, tablolar ve 4 grafik zaten çalıştırılmış hâlde.
  GitHub'da ya da VS Code'da açınca sonuçları kod çalıştırmadan görürsün.
- Kendin çalıştırmak için: VS Code (Jupyter eklentisi), Jupyter ya da Google Colab'da aç,
  hücreleri yukarıdan aşağıya sırayla çalıştır. İlk hücre gerekli paketleri kurar,
  veri internetten otomatik iner. Toplam süre yaklaşık 1 dakika.

## Düz Python: `bess_kolay.py`
```
pip install pandas numpy highspy openpyxl matplotlib
python bess_kolay.py
```
Argüman ve veri dosyası gerekmez; veriyi kendisi indirir, sonuçları yazar,
grafikleri gösterir ve `bess_sonuclar.xlsx` dosyasını kaydeder.
Varsayımlar dosyanın başındaki `V = {...}` sözlüğünde.

> Not: `bess_analiz.py` komut satırı aracıdır, `--veri dosya.csv` olmadan çalışmaz.
> Python konsoluna ya da Jupyter'e yapıştırırsan hata verir. Kopyala-yapıştır için
> `bess_kolay.py` ya da defteri kullan.

---

# bess_analiz.py — nasıl kullanılır

## 1. Kurulum (bir kere)
```
pip install pandas numpy highspy openpyxl
```

## 2. Veriyi indir
EPİAŞ Şeffaflık Platformu → Elektrik → Gün Öncesi Piyasası → **Piyasa Takas Fiyatı (PTF)**.
Saatlik, bir yıllık aralık seç, **CSV** olarak indir. Dosyanın ilk satırı şöyle olmalı:
```
Tarih;Saat;PTF (TL/MWh);PTF (USD/MWh);PTF (EUR/MWh)
```

## 3. Çalıştır
```
python bess_analiz.py --veri Piyasa_Takas_Fiyati-25042025-25042026.csv
```
Seçenekler:
- `--baslangic 2025-04-25 --bitis 2026-04-24` → belirli bir dönem (boşsa son 8.760 saat)
- `--esik` → 5 yıl geri ödeme için gereken primer fiyatını da bulur (12 çözüm, birkaç dakika)
- `--cikti sonuclarim.xlsx` → Excel çıktısının adı
- Birden fazla dosya verebilirsin: `--veri 2024.csv 2025.csv`

## 4. Varsayımları değiştir
Dosyanın başındaki `VARSAYIMLAR` sözlüğü. En önemlileri:

| Anahtar | Şu anki değer | Ne zaman değiştir |
|---|---|---|
| `pfk_fiyat` | 1879 | TEİAŞ'tan gerçek primer fiyatı gelince |
| `sfk_fiyat` | 2000 | Güncel sekonder fiyatıyla |
| `kur` | 50 | Kur değişince |
| `enerji_usd_kwh`, `guc_usd_kw` | 95, 170 | Tedarikçi teklifleri gelince |
| `santral_min_mw`, `santral_max_mw` | 250, 350 | Santralin gerçek çalışma aralığı |
| `santral_mc` | 1500 | Yakıt marjinal maliyeti netleşince |

Tek bir senaryoyu kendin denemek için Python içinden:
```python
from bess_analiz import ptf_yukle, coz, VARSAYIMLAR
p = ptf_yukle(["dosya.csv"]).iloc[-8760:].values
r = coz(p, VARSAYIMLAR, batarya_mw=20, batarya_mwh=30, pfk_fiyat=800)
print(r)
```
`coz(...)` içine `VARSAYIMLAR`'daki herhangi bir anahtarı yazarak o senaryo için değiştirebilirsin
(ör. `kur=62`, `sfk_fiyat=1112`, `pfk_pazar_max=10`).

## 5. Sonuçları okuma
- **portföy net:** santral + bataryanın, bugünkü duruma göre yıllık ek kârı (M TL)
- **batarya katkısı:** portföy net − bataryasız durum → bataryanın kendi getirdiği
- **geri ödeme:** batarya yatırımı ÷ batarya katkısı
- Bataryasız satır = santralin yalnız sekonder tutmasının değeri (yatırımsız)

## Modelin sınırları (bilerek basit tutuldu)
- Kusursuz öngörü: model yılın fiyatlarını önceden biliyor. Al-sat için %85 düzeltme var, yan hizmetlerde yok.
- Primer ve sekonder fiyatları yıl boyu sabit varsayılıyor; gerçek saatlik seri yok.
- Santralin rampa hızı, kısmi yük verim kaybı ve aşınması modelde yok.
- TEİAŞ enerji kuralları ikincil kaynaktan; resmî metinle teyit edilmeli.
