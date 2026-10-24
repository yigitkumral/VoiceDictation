# Belgeler

VoiceDictation için tek TODO ve CHANGELOG tutulur; büyük projelerin sprint ve günlük indeksleri çoğaltılmaz.

- Kök README: kurulum, kullanım ve yerel dosyaların tek envanteri.
- CLAUDE.md: her oturumda gereken proje kuralları; ortak kurallar kullanıcı düzeyindedir.
- [TODO.md](TODO.md): açık işler ve ertelenen fikirler.
- [CHANGELOG.md](CHANGELOG.md): tamamlanan işler ve kararlar, en yeni üstte.
- [nasil-calisir.md](nasil-calisir.md): güncel davranış, modlar ve çıktı biçimi.
- [mimari.md](mimari.md): konuşma kaynağı, Whisper/Qwen ve son odaktaki alana yapıştırma şeması.
- [dikte-akisi.html](dikte-akisi.html): tıklanabilir kullanım akışı, kaynak senaryoları, tam model promptları ve bellek sınırları.
- [kurulum.md](kurulum.md): platform kurulumu, izinler ve cihaz taşıma.
- [calibration/](calibration/README.md): okuma metni ve ölçüm yöntemi.
- [sessions/](sessions/README.md): kapsamlı incelemelerin plan, karar ve kanıtları; rutin değişiklik için klasör gerekmez.

Oturum kaydı yeni iş yetkisi değildir. Eski kayıtlar korunur. Ham ses, transkript, log, sır ve kişisel adresler
belgelere kopyalanmaz. Geçici test çıktısı `.local/` altında tutulur. Dosya adları ASCII ve tireli,
belge metni Türkçe ve UTF-8 olur. Kullanım veya yol değişince ilgili canlı belge aynı değişiklikte güncellenir.
