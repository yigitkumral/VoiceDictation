# Uygulama kaynakları

| Kaynak | İşlev |
|---|---|
| `dictation.py` | Ana süreç, ses kaydı, Whisper, temizlik, kısayollar ve menü |
| `context_bridge.py`, `context_source.py` | Doğrulanmış sohbet kaynağını okuma ve bağlam önbelleği |
| `remote_dictation.py` | Vault üzerinden gelen telefon/tablet dikte istekleri |
| `diagnostics.py` | Yerel tanı kayıtları |
| `mac_trackpad.py`, `mac-trackpad/` | Aynı süreçte çalışan Mac dört parmak algılayıcısı |
| `file_queue.py` | Henüz daemon'a bağlı olmayan dosya kuyruğu |

Repo kökünden `.local/venv/Scripts/python -m dev.dictation` (Windows) veya `.local/venv/bin/python -m dev.dictation` (Mac) ile başlatılır. Kökte ayrı giriş dosyası yoktur. Normal kullanımda `scripts/` altındaki başlatıcılar Python önbelleğini de `.local/__pycache__/` altına yönlendirir.

Veri, modeller, Python ortamı ve yerel çalışma çıktıları repo kökündeki `.local/` altındadır. Bu geliştirme ağacında işletim komutları `scripts/`, testler `tests/`, bağımlılıklar `requirements.txt` içindedir. Test komutu: `.local/venv/Scripts/python -B -m unittest discover -s dev/tests` (Mac'te `Scripts/python` yerine `bin/python`).
