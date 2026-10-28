Model: GPT-6 tabanlı Codex (daha ayrıntılı model kimliği oturumda bildirilmedi).

## Sonuc

`_WORD_CORRECTIONS` içinde beş dar düzeltme tamamlandı: TestSlight/TestSplight/Test Slight/test slide/Test Flight → TestFlight; hurdler → Herdr; ClotCode/Clot Code/KlotKod → Claude Code; tam Pushet → push et; iphone-zo/Iphone Zoan/iFoz → iFonzo. Büyük/küçük harf varyasyonları ve kesmeyle ayrılmış Türkçe ekler korunuyor. Her kuralın üstüne Windows/Vault, 28 Eki 2026 kaynak yorumu eklendi.

## Testler

- `.local/venv/bin/python -m unittest discover -s dev/tests`: **228 test geçti**, 7,148 sn.
- `.local/venv/bin/python -m py_compile dev/dictation.py`: başarılı.
- `git diff --check`: temiz.

`test_prompt_budget.py` içinde her kural için olumlu, düz/akıllı kesmeyle ekli ve olumsuz örnekler eklendi. Önceki iPhone ve Cloud olumsuz testleri korunuyor; kapsam dışındaki adlar ve Title Case ayrıca sınandı.

## Kararlar

Yeni kalıplar tam kelime sınırlarıyla eşleşiyor; kesmesiz bitişik ekler genişletilmedi. Claude Code bileşik kuralı mevcut Claude kurallarından önce çalışıyor; Cloud istisnası değişmedi. iFonzo'nun önceki biçimleri korunarak yalnız dar alternatifler eklendi; tireli yeni biçim `e-zo` ile sınırlandı. `_apply_word_corrections` değiştirilmedi.

## Acik

Kod/test kapsamında açık iş yok. Ana ajan tamamlanan kuralları CHANGELOG'a ekleyebilir; sonuç dosyası dışında belge değiştirilmedi. Daemon/model başlatılmadı, commit/push yapılmadı.

hazir | /Users/yigitkumral/Desktop/Yazilim/VoiceDictation/docs/sessions/2026-10-28-dikte-kalite/sonuc/tur3.md
