# Görev — opus-ortam (çalışma ortamı, yerel bağımlılıklar, taşınabilirlik)

Önce aynı klasördeki `ortak-brif.md` dosyasını oku; kararlar ve kurallar orada. Sonuç dosyan: `sonuc-ortam.md`.

## Odak: kod dışındaki her şey — Mac'e taşınırsa ne olur

- **venv:** 2,8 GB; CUDA DLL'leri venv içinden PATH'e ekleniyor (`dictation.py:150`+). `requirements.txt` (91 byte) ve `scripts/setup.*` bugünkü ortamı kurabiliyor mu? Windows CUDA ↔ Mac MLX ayrımı kurulumda nasıl ele alınıyor?
- **Model önbelleği:** Whisper modelleri `~/.cache/huggingface/hub/` altında (`HF_HOME` tanımsız). Repo içine alınsın mı (`download_root` / `HF_HOME` ile) yoksa kullanıcı önbelleğinde kalıp **belgelensin** mi? Artıları/eksileri (yedek boyutu, çoklu proje paylaşımı, Mac'te MLX modelleri farklı repo). 4,8 GB **referanssız** model (large-v3, medium, small) ve speechbrain çift kopyası (`~/.cache` + `<repo>/models/`) — ne yapılmalı, Yiğit'e **soru** olarak yaz.
- **Log ve durum dosyaları:** `logs/` 157 dosya, sınırsız birikim (`backupCount=0`, `:130`+), PID lockfile `logs/dictation.pid`, kökteki eski `dictation.log`. Basit bir saklama kuralı gerekir mi? Loglar kişisel veri içeriyor mu (yalnız ne loglandığını koddan çıkar; log içeriği okuma).
- **Başlangıç:** Windows Startup klasöründeki `start.vbs` repo'daki dosyanın **kopyası** ve yolu sabit; Mac `scripts/VoiceDictation.app` + `docs/auto-start.md`. Taşınabilir ve tek kaynaklı yapı için öneri (kısayol mu, kopya mı, kurulum betiği mi).
- **Yedek etkisi:** `Yazilim` ağacı rclone ile Drive'a günlük yedekleniyor; filtre `C:\Users\yigit\Desktop\Yazilim\_yedek-config\rclone\filter-yazilim.txt` (`venv/` hariç; `logs/`, `models/`, `.local/` dahil). ~1 GB ses + transkript repo ağacına gelince yedek ne yapar (zaten Drive'da olan veri tekrar Drive'a gider); hangi klasörler filtreye eklenmeli — **öneri**, filtreye dokunma.
- **MacBook'a taşıma kontrol listesi:** neler kopyalanır (veri, `.env`?), neler yerinde yeniden üretilir (venv, modeller, başlangıç kaydı, izinler), hangi belge bunu anlatmalı. CLAUDE.md §0.5 / TODO.md'deki Mac doğrulama borcu ile ilişkisi.
- **Gizli kalması gerekenler:** `.env` (HF token), `.mcp.json`, `.claude/settings.local.json` — hedef yapıda ve gitignore'da yerleri.

Uygulama yok, kurulum yok, pip yok; yalnız gözlem ve öneri.

## Geri çağrı (bitince, tek sefer)

1. `ListAgents` aracıyla `voicedictation-67 [231d1e]` oturumunun listede olduğunu gör.
2. `SendMessage` ile `to: voicedictation-67`, mesaj: `hazir: C:\Users\yigit\Desktop\Yazilim\VoiceDictation\docs\yapi-sadelestirme-2026-09-16\sonuc-ortam.md`
3. Gönderim hata verirse yalnız şu koşulda yedek yol: `herdr agent get voicedictation-scope` çıktısında `agent_status` `idle` veya `done` ise `herdr agent prompt voicedictation-scope 'hazir: <yol>'`. `working`/`blocked` ise gönderme, pane'de bekle.

Sonra oturumu kapatma.
