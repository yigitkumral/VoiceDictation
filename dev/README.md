# Uygulama kaynakları

| Kaynak | İşlev |
|---|---|
| `dictation.py` | Ana süreç, ses kaydı, Whisper, temizlik, kısayollar ve menü |
| `context_bridge.py`, `context_source.py` | Doğrulanmış sohbet kaynağını okuma ve bağlam önbelleği |
| `remote_dictation.py` | Vault üzerinden gelen telefon/tablet dikte istekleri |
| `diagnostics.py` | Yerel tanı kayıtları |
| `mac_trackpad.py`, `mac-trackpad/` | Aynı süreçte çalışan Mac üç parmak algılayıcısı |
| `file_queue.py` | Henüz daemon'a bağlı olmayan dosya kuyruğu |

Repo kökünden `venv/Scripts/python dictation.py` (Windows) veya `venv/bin/python dictation.py` (Mac) ile başlatılır. Kökteki giriş dosyası bu paketi çalıştırır; kaynakları doğrudan dosya olarak çalıştırmak gerekmez. Modül girişi de `python -m dev.dictation` biçimindedir.

Veri ve modeller bu klasöre yazılmaz; repo kökündeki `data/` ve `.local/` kullanılır. İşletim komutları `scripts/`, testler `tests/` altındadır.
