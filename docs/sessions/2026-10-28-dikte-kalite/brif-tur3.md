# Brif: Tur 3 — yalniz yuksek kesinlikli ad duzeltmeleri

Isteyen: Yigit. Bas ajan: voicedictation (w1V:p1). Bu brif Tur 1'i yapan pane'e ikinci tur olarak gelir; Tur 1 degisiklikleri
calisma agacinda (commit edilmis ya da edilmemis olabilir), onlari geri alma.
Calisma klasoru: /Users/yigitkumral/Desktop/Yazilim/VoiceDictation (dal master).

Arka plan: dev/dictation.py `_WORD_CORRECTIONS` / `_apply_word_corrections` ve dev/tests/test_prompt_budget.py'deki
word-correction testleri. Ilke: Whisper'in gercek kullanimla karisabilecek biçimleri degistirilmez; yalniz dilde baska
anlami olmayan, kayitlarda tekrar goruldugu dogrulanmis biçimler. Turkce ekler korunur (ornek: `TestSlight'a` ->
`TestFlight'a`). Kosulsuz genis eslesme yok.

Eklenecekler (24-28 Ekim kayitlarinda goruldu):
1. TestFlight: `TestSlight`, `TestSplight`, `Test Slight`, `test slide`, `Test Flight`, `test flight` -> `TestFlight`.
   Tek basina `Slight`, `slide`, `flight` degismez.
2. Herdr: `hurdler`, `Hurdler` -> `Herdr` (ekleriyle).
3. Claude Code: `ClotCode`, `Clot Code`, `KlotKod` gibi birlesik/bitisik bicimler -> `Claude Code`; mevcut Claude
   kurallariyla (Tur 1'deki Cloud istisnasi dahil) celismesin.
4. push et: `Pushet`, `PUSHET`, `pushet` -> `push et` (yalniz bu tam kelime; `pushed`, `pushes` degismez).
5. iFonzo: mevcut iFonzo regex'ini genislet: `iphone-zo`, `iPhone-zo`, `Iphone Zoan`, `iFoz` -> `iFonzo` (ek korunur).
   `iPhone'su`, `iPhone 0`, `iPhone's`, tek basina `iPhone`, `iPhone so`, `iPhones oldu` degismez (mevcut olumsuz
   testler korunur).

Eklenmeyecekler (bilincli karar, dokunma): pane/Payne/pain, Vault/Volt, worktree/work tree, Gemini/Cemilay,
Atelier'in ek almis bicimleri (ateliyede), Title Case kucultme.

Dosya sahipligi: dev/dictation.py (yalniz `_WORD_CORRECTIONS` bolgesi), dev/tests/test_prompt_budget.py (ya da mevcut
word-correction testinin bulundugu dosya). Belgeleri degistirme. Kod yorumlari mevcut uslupla ASCII Turkce; her kural
ustunde kisa kaynak yorumu (mevcut "Mac/Vault (27 Eki 2026): ..." biciminde, tarih 28 Eki 2026, Windows/Vault).
Sinirlar: Tur 1 brifindekiyle ayni (commit/push yok, daemon yok, `.local` veri/log/diagnostics icerigi yok, ag ve dis
gonderim yok, ajan/pane acma yok).
Kabul kontrolu: her eklenen kural icin olumlu (ekli bicim dahil) ve olumsuz test; `.local/venv/bin/python -m unittest
discover -s dev/tests` tamamen gecer; `python -m py_compile dev/dictation.py`.

Sonuc dosyasi: /Users/yigitkumral/Desktop/Yazilim/VoiceDictation/docs/sessions/2026-10-28-dikte-kalite/sonuc/tur3.md.
Ilk satirda gercek modelin. Bicim (yarim sayfa): `## Sonuc` `## Testler` `## Kararlar` `## Acik`.
Bitis: son satira `hazir | <sonuc yolu>`, ekrana ayni satiri yaz ve dur. Soru/engelde `soru | ...` / `engel | ...`.
