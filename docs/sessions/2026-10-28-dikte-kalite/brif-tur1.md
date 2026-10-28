# Brif: Tur 1 — kesin ve dusuk riskli dikte duzeltmeleri

Isteyen: Yigit. Bas ajan: voicedictation (w1V:p1). Pane etiketi ve sohbet adin: VoiceDictation-dikte-tur1-Mac (degistirme).
Calisma klasoru: /Users/yigitkumral/Desktop/Yazilim/VoiceDictation (dal master). Ayni klasorde paralel olarak baska bir
ajan Tur 2'yi yapiyor (dev/context_source.py, dev/context_bridge.py ve testleri); o dosyalara dokunma.

Arka plan (once oku): CLAUDE.md, docs/nasil-calisir.md (halusinasyon katmanlari, temizlik), dev/dictation.py ilgili
fonksiyonlar. 24-28 Ekim Windows kayit analizi ve capraz gorus su sorunlari cikardi:

Gorevler (hepsi dev/dictation.py; her biri icin test):
1. **Son noktalama:** `_clean_transcription` 10+ kelimelik dalda `re.sub(r"^[\s.,;:!?]+|[\s.,;:!?]+$", "", cleaned)`
   sondaki `.?!` isaretlerini de siliyor; Qwen reddedince ya da metin >1200 karakter olunca son metin noktalamasiz ve
   soru isaretsiz kaliyor (diktelerin ~%40'i). Bastaki noktalama ve sondaki `,;:` silinmeye devam etsin; sondaki
   anlamli `.`, `?`, `!`, `…` korunsun (birden cok nokta/`..` gibi artiklari tek isarete indirmek serbest, `?!` gibi
   anlamli bileskeler korunur). `_strip_known_artifacts` (toplanti/dosya yolu) degismesin.
2. **Ret/atlama sebep kodu:** `_cleanup_text` su an yalniz `status` (accepted/rejected/oversize/...) yaziyor. Reddedilen
   adayda ilk takilan kurali icerik olmadan bir kod olarak kaydet (orn. `reason`: `empty`, `length`, `control`,
   `numbers`, `literals`, `symbols`, `words`, `question`, `quote`). Bunun icin `_accept_cleanup`'in davranisini
   degistirmeden sebebi dondurebilen bir ic yardimci kur; `_accept_cleanup(original, candidate) -> bool` imzasi ve
   mevcut testleri korunur. Kod `cleanup_stats.value` uzerinden zamanlama/metrik kaydina (`timings` ->
   `cleanup_reason` gibi) ve tani kaydina gitsin; Qwen hic calistirilmadiysa (oversize, not_ready, busy, unavailable)
   bu ret sayilmaz, status zaten ayri. Metin/aday icerigi kaydedilmez.
3. **Kisisel ipucu sirasi:** `_whisper_context` icinde `PERSONAL_HINTS` (iFonzo, Zugzwang) yalniz ipucunda yoksa basa
   ekleniyor; listede sonda varsa 40 token kesiminde dusebiliyor. Terimleri alt dize ile degil, virgulle ayrilmis
   liste ogesi olarak karsilastir (buyuk/kucuk harf duyarsiz); kisisel terimleri tekrarsiz basa al, kalan terimleri
   mevcut sirayla arkaya koy, sonra token siniri uygulansin. dev/tests/test_prompt_budget.py'deki ilgili test
   guncellenir/genisletilir (terim sonda iken basa tasinmali).
4. **Cloud -> Claude:** `_WORD_CORRECTIONS` icindeki `(re.compile(r"\b[ck]l[ao]u?[dt]\b", re.I), "Claude")` "Cloud Save
   Files" -> "Claude Save Files" yapti. Ardindan buyuk harfle baslayan bir kelime geliyorsa (Code haric) dokunma:
   "Cloud Save Files", "Cloud Storage", "Cloud Run" korunur; "Cloud", "cloud code", "Claud'a", "Klod" eskisi gibi
   duzelir. Mevcut word-correction testlerine olumlu ve olumsuz ornek ekle.
5. **Kabul kapisina iki kontrol (`_accept_cleanup`):**
   - Soru isareti: ham metindeki (literal disi) her `?` adayda ayni kelimenin ardinda kalmali; "ne durumdayiz?" ->
     "ne durumdayiz." reddedilir. Yeni `?` eklemek serbest (Qwen soruyu duzeltebilir).
   - Tirnak: aday yeni bir dengesizlik yaratamaz. Ham metinde dengeli/hic olmayan cift tirnak (`"`, `“”`) adayda
     dengesiz olamaz; ham metin zaten dengesizse ek kural yok. Kesme isareti (') bu kurala girmez.
   Iki kuralin sebep kodu 2. maddedeki `question` ve `quote` olur.
6. **Kapanis halusinasyonu:** `_ARTIFACT_RE` icindeki `İzlediğiniz için teşekkür\w*` "İzlediğiniz için teşekkür ederim"
   kaliminda "ederim"i birakiyor. Tam kalibi (ederim/ederiz, sondaki noktalama dahil) eslestir; ayni metnin icinde
   gercek konusma olarak gecen "teşekkür ederim"e (kalip disi) dokunma.

Dosya sahipligi: dev/dictation.py; dev/tests/ altinda test_prompt_budget.py, test_cleanup_v3.py, test_dictation.py,
test_diagnostics.py, test_timings.py ve gerekirse yeni test dosyasi. Belgeleri (README, docs/, CHANGELOG) degistirme;
belge degisikligi gerekiyorsa sonucta yaz, bas ajan yapar. Kod yorumlari mevcut uslupla ASCII Turkce, yorum yogunlugu
cevredeki kodla ayni.
Sinirlar: commit/push yok; daemon'u durdurma/baslatma yok, `dev/dictation.py`'yi calistirma yok (yalniz testler ve
`python -m py_compile`); `.local/data`, `.local/logs`, `.local/diagnostics` icerigi okunmaz; sir okuma, kalici silme,
izin/hook/MCP ayari yok; ag erisimi, dis gonderim, ajan/pane acma, baska pane'e yazma yok. Baska oturumun pane/transkripti
okunmaz.
Kabul kontrolu: `.local/venv/bin/python -m unittest discover -s dev/tests` tamamen gecer (paralel Tur 2 ajaninin ara
durumu yuzunden context testleri kirmiziysa bunu ayir ve belirt); `.local/venv/bin/python -m py_compile dev/dictation.py`.
Her gorev icin en az bir olumlu ve bir olumsuz test.

Sonuc dosyasi: /Users/yigitkumral/Desktop/Yazilim/VoiceDictation/docs/sessions/2026-10-28-dikte-kalite/sonuc/tur1.md
(Git'e girer: dikte icerigi, kisisel veri yok). Ilk satirda gercek modelin. Bicim (en fazla bir sayfa, Turkce):
`## Sonuc` (gorev basina ne degisti, fonksiyon adlariyla) `## Testler` (komut ve sonuc sayisi) `## Kararlar`
(brifte acik olmayan secimler) `## Acik` (belge guncellemesi gerekenler dahil).
Bitis: dosyanin son satirina `hazir | <sonuc yolu>` ekle, ekrana ayni satiri yaz ve dur. Soru ya da engelde dosyanin
sonuna `soru | ...` ya da `engel | ...` yaz, ekrana ayni satiri yaz ve dur; cevap bu pane'e gelir.
