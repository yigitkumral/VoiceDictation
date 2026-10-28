Model: GPT-6 tabanlı Codex (daha ayrıntılı model kimliği oturumda bildirilmedi).

## Sonuc

1. `_clean_transcription`: 10+ kelimede sondaki `.?!…` ve `?!` bileşkesi korunuyor; baştaki noktalama ve sondaki `,;:` temizleniyor. `_strip_known_artifacts` fonksiyonu değiştirilmedi.
2. `_cleanup_rejection_reason`: ilk başarısız kural için `empty`, `length`, `control`, `numbers`, `literals`, `symbols`, `words`, `question`, `quote` döndürüyor; kabulde `None`. `_accept_cleanup(original, candidate) -> bool` korunuyor. `_cleanup_text`, `cleanup_stats.value.reason` ve içeriksiz `cleanup_decision` tanı aşamasını dolduruyor. `_send_final` / `_remote_dictate` nedeni `cleanup_reason` olarak ölçümlere ve tanıya taşıyor; `_write_timing` yalnız izinli ret kodlarını yazıyor. Atlanan çağrılar ret sayılmıyor.
3. `_whisper_context`: kişisel terimler virgülle ayrılmış tam öğe ve büyük/küçük harf duyarsız eşleştirmeyle tekilleştirilip başa taşınıyor; diğer öğelerin sırası ve token sınırları korunuyor.
4. `_WORD_CORRECTIONS`: Code hariç büyük harfle başlayan sonraki sözcük korunuyor; Cloud Save Files / Storage / Run değişmiyor. Cloud, cloud code, Claud'a ve Klod düzeltmeleri sürüyor.
5. `_accept_cleanup`: literal dışı soru işaretleri aynı kelimenin aynı tekrarına bağlı kalıyor; yeni soru işareti serbest. Dengeli düz/akıllı çift tırnaklardan dengesiz adaya geçiş reddediliyor; ham metin dengesizse ek kısıt yok, kesme işareti kapsam dışı.
6. `_ARTIFACT_RE`: kapanış kalıbının ederim/ederiz devamı ve son noktalaması birlikte siliniyor; kalıp dışındaki gerçek teşekkür korunuyor.

## Testler

- `.local/venv/bin/python -m unittest discover -s dev/tests`: **222 test geçti**, context testleri dahil; 6,954 sn.
- `.local/venv/bin/python -m py_compile dev/dictation.py`: başarılı.
- `git diff --check`: temiz. Eski yol adları denetimi boş döndü.
- Her görev için olumlu/olumsuz örnekler; ayrıca masaüstü/uzak dikte neden aktarımı, kod beyaz listesi, atlama sonrası neden sıfırlama, ret/1200+ karakter dönüşünde noktalama ve literal kontrolleri eklendi. Daemon/model başlatılmadı; gerçek ses kabulü yapılmadı.

## Kararlar

- Sondaki çoklu noktalar aynen korundu. Kişisel ipucu önceliği mevcut konuşma bağlamı yolunda uygulandı; statik ipucu davranışı korunuyor.
- Ret önceliği eski filtre sırasını izliyor; yeni soru ve tırnak denetimleri kelime denetiminden sonra geliyor. Soru konumu kelime hizalamasıyla kontrol ediliyor; izinli dolgu/gün silmeleri soru işaretini silemiyor.
- Yeni ret kaydı yalnız durum/neden kodu taşıyor; mevcut izinli ayrıntılı tanının içerik alanları değiştirilmedi. Sentetik benchmark yakalayıcısı yeni yardımcıya uyarlandı.

## Acik

- Ana ajan: `docs/nasil-calisir.md` temizlik/ölçüm açıklamalarına soru ve tırnak koruması ile neden kodlarını; `docs/CHANGELOG.md` dosyasına tamamlanan altı düzeltmeyi eklemeli. README ölçüm özeti de neden kodlarına değinebilir. Bu turda belgeler sonuç dosyası dışında değiştirilmedi.
- Gerçek mikrofon ve modelle kullanım kabulü bu turun dışında. Commit/push yapılmadı; Tur 2 dosyalarına dokunulmadı.

hazir | /Users/yigitkumral/Desktop/Yazilim/VoiceDictation/docs/sessions/2026-10-28-dikte-kalite/sonuc/tur1.md
