# Brif: Tur 2 — Whisper'a giden sohbet baglaminin temizligi

Isteyen: Yigit. Bas ajan: voicedictation (w1V:p1). Pane etiketi ve sohbet adin: VoiceDictation-dikte-tur2-Mac (degistirme).
Calisma klasoru: /Users/yigitkumral/Desktop/Yazilim/VoiceDictation (dal master). Ayni klasorde paralel olarak baska bir
ajan Tur 1'i yapiyor (dev/dictation.py ve diger testler); o dosyalara dokunma.

Arka plan (once oku): CLAUDE.md (Dikte davranisi, Baglam kaynagi), docs/mimari.md (baglam kaynagi), dev/context_bridge.py
(`_visible_text`, `build_hints`), dev/context_source.py (`_snapshot`, `_LABELS`, `_REMOTE_EXPORT`, `ContextCache`),
dev/dictation.py `_whisper_context` (yalniz oku). Sohbet modunda aktif terminal sohbetinin son ~160 token'i Whisper'a
`initial_prompt`, `build_hints` ciktisi 40 token `hotwords` olarak gider. Vault (iPhone) ve masaustu ayni `_snapshot`
temizliginden gecer.

Sorun (24-28 Ekim Windows kayitlari): Whisper'a giden sohbet metninde Markdown kalin (`**...**`), basliklar, tablo
cizgileri ve arac cerceveleri (`<task-notification>...</task-notification>`, `<local-command-stdout>...`) var; Whisper bu
bicimi dikteye kopyaliyor (bir gunde 8/163 kayitta ciktida `**`). Etiketler token butcesini de yiyor.

Gorev:
1. Sohbet metni kesilmeden ve ipucu cikarilmadan once (ayni temizlik hem `text` hem `build_hints` girdisine yansisin),
   tek yerde ve yerel/SSH/Vault yollarinin hepsini kapsayacak bicimde temizle. Tercih `context_source._snapshot`
   (mevcut `_LABELS` temizliginin yanina); `context_bridge._visible_text`'e girmen gerekiyorsa gerekcesini yaz.
2. Atilacaklar (kelimeler kalir, yalniz bicim gider):
   - Markdown vurgu isaretleri `**`, `__` ve kelime cevresindeki tek `*`/`_` (snake_case, `a*b` gibi kodlar bozulmaz);
   - satir basi `#` baslik isaretleri, `>` alinti isareti, liste imleri (`- `, `* `, `1. `), tablo ayiraclari
     (`|---|---|` satiri tamamen; hucre ayiraci `|` bosluga);
   - kod citleri ``` ve satir ici backtick: isaretler gider, icindeki ad/yol/komut kalir;
   - arac cerceveleri: `<task-notification>...</task-notification>`, `<local-command-stdout>...</local-command-stdout>`,
     `<local-command-stderr>...` bloklari icerikleriyle birlikte gider (kapanmamis blok metin sonuna kadar);
   - diger acilis/kapanis etiketleri (orn. `<pasted_content id="12">`): yalniz etiket gider, icerik (kullanicinin
     kendi metni) kalir.
3. Yeni temizlik kelime sayimini (`words`, `MAX_WORDS`) bozmasin; bos kalan mesaj atlansin. `build_hints` ciktisinda
   `task`, `notification`, `stdout` gibi cerceve kelimeleri gorulmesin.

Dosya sahipligi: dev/context_source.py, dev/context_bridge.py, dev/tests/test_context_source.py,
dev/tests/test_context_bridge.py (gerekirse dev/tests/test_context.py; dokunursan sonucta yaz). Belgeleri degistirme;
gerekiyorsa sonucta yaz, bas ajan yapar. Kod yorumlari mevcut uslupla ASCII Turkce.
Sinirlar: commit/push yok; daemon'u durdurma/baslatma yok, `dev/dictation.py`'yi calistirma yok; `.local/data`,
`.local/logs`, `.local/diagnostics` icerigi okunmaz; gercek sohbet transkriptleri okunmaz, testlerde uydurma ornek
kullan; sir okuma, kalici silme, izin/hook/MCP ayari yok; ag erisimi, dis gonderim, ajan/pane acma, baska pane'e yazma
yok. Baska oturumun pane/transkripti okunmaz.
Kabul kontrolu: `.local/venv/bin/python -m unittest discover -s dev/tests` gecer (paralel Tur 1 ajaninin ara durumu
yuzunden dictation testleri kirmiziysa bunu ayir ve belirt); her atilan bicim icin test, ayrica korunmasi gereken
ornekler (snake_case, dosya yolu, `a*b`, kod citi icindeki ad, `<pasted_content>` icerigi) icin test.

Sonuc dosyasi: /Users/yigitkumral/Desktop/Yazilim/VoiceDictation/docs/sessions/2026-10-28-dikte-kalite/sonuc/tur2.md
(Git'e girer: kisisel veri yok). Ilk satirda gercek modelin. Bicim (en fazla bir sayfa, Turkce): `## Sonuc`
`## Testler` `## Kararlar` `## Acik` (belge guncellemesi gerekenler dahil).
Bitis: dosyanin son satirina `hazir | <sonuc yolu>` ekle, ekrana ayni satiri yaz ve dur. Soru ya da engelde dosyanin
sonuna `soru | ...` ya da `engel | ...` yaz, ekrana ayni satiri yaz ve dur; cevap bu pane'e gelir.
