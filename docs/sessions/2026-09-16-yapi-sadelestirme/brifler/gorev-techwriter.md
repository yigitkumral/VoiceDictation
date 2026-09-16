# Görev — opus-techwriter (BMAD Tech Writer kimliğiyle)

Önce aynı klasördeki `ortak-brif.md` dosyasını oku; kararlar ve kurallar orada. Sonuç dosyan: `sonuc-techwriter.md`.

## Kimlik

Skill aracıyla `bmad-tech-writer` skill'ini yükle ve **o kimlikle** çalış (teknik yazar / belge mimarı). Karşılama, menü veya seçim sunma; doğrudan bu görevi yap. Yiğit senin mesleki yargını özellikle önemsiyor — diğer ajanlardan bağımsız, net ve kararlı öner; "olabilir/belki" yerine "şöyle olsun, çünkü".

## Odak: belgeler ve yapının okunabilirliği

- **Devir testi:** Proje MacBook'a taşınıp yeni bir ajan (veya Yiğit'in kendisi, aylar sonra) açtığında **5 dakikada** neyi bilmeli? Şu anki `CLAUDE.md` (16 KB), `README.md` (14 KB), `CHANGELOG.md`, `TODO.md`, `docs/auto-start.md`, `G:\Drive'ım\Records\index.md` bu testi geçiyor mu? Nerede tekrar, nerede eskimiş bilgi, nerede karışan sorumluluk var (kanıt: dosya + bölüm başlığı)?
- **Yerel bağımlılık haritası:** venv, model önbelleği, log, veri (transkript/ham ses), Meet girdi klasörü, geçici dosyalar, başlangıç kaydı (Windows/Mac) — bunlar **tek bir yerde, tek tabloda** nasıl belgelenir? Hangi belgede durmalı?
- **Belge seti önerisi:** iFonzo'nun düzeniyle (`CLAUDE.md` = ajan talimatı, `README.md` = insan girişi, `docs/` = TODO/changelog/arşiv) karşılaştır. VoiceDictation için hangi belgeler kalsın, hangileri birleşsin/taşınsın; her belgenin **tek cümlelik görevi**. `CLAUDE.md`'de ne kalır (ajanın her oturumda bilmesi gereken kısa kurallar), ne `README`/`docs`'a gider (tarihçe, akış anlatımı, Mac izinleri gibi uzun içerik)?
- **Adlandırma:** Türkçe/İngilizce karışımı klasör ve dosya adları (VoiceDictation, RawRecords, calibration, docs, logs) için tutarlı ve kısa bir kural öner.
- **Kodla belge tutarlılığı:** belgelerde anlatılan yollar/klasörler kodla örtüşüyor mu (örn. CLAUDE.md'deki `Meet Recordings\RawRecords\` artık yok)? Uygulama sonrası belgelerin güncel kalması için basit bir kural.

Kod ayrıntısına girme; kodu yalnız belgelerin doğruluğunu kontrol etmek için oku.

## Geri çağrı (bitince, tek sefer)

1. `ListAgents` aracıyla `voicedictation-67 [231d1e]` oturumunun listede olduğunu gör.
2. `SendMessage` ile `to: voicedictation-67`, mesaj: `hazir: C:\Users\yigit\Desktop\Yazilim\VoiceDictation\docs\yapi-sadelestirme-2026-09-16\sonuc-techwriter.md`
3. Gönderim hata verirse yalnız şu koşulda yedek yol: `herdr agent get voicedictation-scope` çıktısında `agent_status` `idle` veya `done` ise `herdr agent prompt voicedictation-scope 'hazir: <yol>'`. `working`/`blocked` ise gönderme, pane'de bekle.

Sonra oturumu kapatma; Yiğit seninle konuşmak isteyebilir.
