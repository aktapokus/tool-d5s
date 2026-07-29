# Digital 5S — Kullanım Kılavuzu

Digital 5S, bilgisayarınızdaki dağınık bir klasörü sizin için toplayıp düzenleyen bir asistandır. Ne yapmak istediğinizi kendi cümlelerinizle yazarsınız, o size bir öneri listesi çıkarır, siz onaylarsınız, o da uygular.

## Nasıl kullanılır — 4 adım

**1. Bir klasör seçin**
"Klasör" kutusunun yanındaki **Seç** butonuna tıklayın, bilgisayarınızdaki bir klasöre gidin, seçin.

**2. Ne istediğinizi yazın**
"İstek" kutusuna, sanki bir arkadaşınıza anlatır gibi yazın. Örnekler:
- "Eski dosyaları arşive at"
- "Geçici dosyaları temizle"
- "Word dosyalarını bir klasörde topla"
- "Boş klasörleri sil"

Teknik terim kullanmanıza gerek yok — sade Türkçe yeterli.

**3. Analiz Et'e basın ve öneriyi inceleyin**
Program klasörünüzü tarar, bir öneri listesi ve bir **5S skoru** (klasörünüzün ne kadar düzenli olduğunun bir ölçüsü, A'dan F'ye) gösterir. Her öğenin yanında neden önerildiği yazar.

**Hiçbir şey otomatik uygulanmaz.** Siz onaylamadan hiçbir dosyaya dokunulmaz.

**4. İstediklerinizi seçip Uygulayın**
Her öneri satırının yanında bir kutucuk var — istemediğinizi işaretten çıkarabilirsiniz. Faz filtrelerini (Seiri, Seiton, Seiso...) kullanarak sadece belirli türdeki önerileri görebilirsiniz. Hazır olduğunuzda **Seçileni Uygula**'ya basın.

## 5S nedir, skorlar ne anlama gelir

Bu, fabrikalarda kullanılan bir düzen/temizlik metodolojisinin dosyalara uyarlanmış hali:

| Faz | Anlamı |
|---|---|
| **Seiri** (Ayıklama) | Gereksiz/eski dosyaları bulur |
| **Seiton** (Düzenleme) | Dosyaları konularına göre gruplar |
| **Seiso** (Temizlik) | Geçici/önbellek dosyalarını temizler |
| **Seiketsu** (Standart) | Klasör yapısının tutarlılığını ölçer |
| **Shitsuke** (Sürdürme) | Düzenin kalıcı olup olmadığını izler |

Her faz için 0-100 arası bir puan, toplamda da bir harf notu (A-F) görürsünüz. Düşük puan "kötü" demek değil, sadece "bu alanda iyileştirilecek çok şey var" demektir.

## Bir hata yaptıysanız — Geri Al

Bir işlemi uyguladıktan sonra fikrinizi değiştirdiyseniz, **Son İşlemi Geri Al** butonuna basın. Program son işlemi geri alır — taşınan dosyalar eski yerine döner. (Silinen dosyalar geri alınamaz, bu yüzden silme önerilerini onaylarken bir kez daha göz atmanızı öneririz.)

Bu buton, sayfayı kapatıp tekrar açsanız bile çalışır — geçmiş işlemleriniz kalıcı olarak kaydedilir.

## Rapor indirme

Analiz sonucunun altındaki **HTML Rapor İndir** butonuyla, o analizin tam raporunu bilgisayarınıza indirebilir, daha sonra incelemek veya paylaşmak için saklayabilirsiniz.

## Sık sorulan sorular

**Program klasörümü izinsiz mi değiştiriyor?**
Hayır. Hiçbir dosya, siz açıkça "Seçileni Uygula"ya basmadan değişmez.

**Yanlışlıkla önemli bir dosyayı sildirdim mi diye endişeleniyorum.**
Silme önerileri her zaman düşük risk (`low`) etiketiyle gelir ve nedeni açıkça yazılıdır. Emin olmadığınız bir öneriyi işaretten çıkarıp uygulamayabilirsiniz.

**"Bağlantı hatası" görüyorum.**
Bu genellikle yapay zeka modelinin (LLM) meşgul olduğu ya da henüz hazır olmadığı anlamına gelir — birkaç saniye bekleyip tekrar deneyin.
