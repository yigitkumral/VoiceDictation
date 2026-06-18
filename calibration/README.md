# Kalibrasyon — VoiceDictation

Bu klasör, Whisper transkripsiyon hatalarını **log madenciliği yerine tek bir sesli okumayla** hızlıca yakalamak için kullanılır.

## Mantık

`reference_tr.txt` = **ground truth** (doğru metin). Bu metni sesli okursun, Whisper transkribe eder, ardından referans ↔ çıktı `jiwer` ile hizalanır. Çıkan substitution sözlüğü (`doğru → Whisper'ın yazdığı`) bize otomatik olarak şunları önerir:

- `_WORD_CORRECTIONS` regex eklemeleri (sonradan-düzeltme katmanı)
- `INITIAL_PROMPT` / `hotwords` kelime eklemeleri (decode-anı biasing)

## Metin neyi içeriyor

- **Senin gerçek konuşma stilin:** uzun, dolgulu (mesela, aslında, yani), İngilizce teknik terim gömülü Türkçe cümleler — log korpusundan (3466 dikte) ve Claude Code sohbet geçmişinden damıtıldı.
- **Kronik hata terimleri** (her biri en az bir kez, gömülü): Atelier, NotebookLM, VoiceDictation, Claude/Claude Code, Zugzwang, Obsidian, Notion, docs, PRD/FR/NFR, ETL, pipeline, MCP, BMAD, Sonar/Tivibu, Govinet, Dizipal, DMCA, delisting, Figma, Excel, ChatGPT, Gemini, CUDA, daemon, PID, watchdog.
- **Rakam telaffuzu** (son paragraf) — sayı transkripsiyonunu da kalibre eder.

## Nasıl kullanılır (planlanan akış)

1. `reference_tr.txt`'i normal hızında, doğal tonunla sesli oku.
2. `dictation.py --calibrate` (henüz yazılmadı — sıradaki adım) sesi alır, beam=5 transkribe eder.
3. `jiwer` ile diff → `calibration/proposed_corrections.md` üretilir (substitution tablosu + WER% + önerilen regex/hotwords).
4. **Sen incelersin**, onayladıklarını koda işleriz. Otomatik uygulanmaz — yanlış bir regex iyi transkripsiyonu bozabilir.

## Önemli

- Metin **birebir** okunmalı; cümle atlarsan diff bozulur (jiwer ekleme/silme olarak işaretler, yine de tolere eder ama temiz okuma daha iyi sonuç verir).
- Jargonu güncellersen metni de güncelle, tekrar oku, WER düşüşünü ölç.
