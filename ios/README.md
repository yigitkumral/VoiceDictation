# VoiceDictation iOS

Masaüstü VoiceDictation uygulamasının minimal iOS versiyonu. WhisperKit ile lokal Whisper modeli kullanarak konuşmayı metne çevirir.

## Gereksinimler

- Xcode 15.0+
- iOS 16.0+
- iPhone (mikrofon erişimi gerekli — Simulator'da çalışmaz)

## Kurulum

### 1. Xcode ile Açma

```bash
cd ios/VoiceDictation
open Package.swift
```

Xcode, `Package.swift` dosyasını açtığında WhisperKit bağımlılığını otomatik indirecektir.

### 2. Xcode Projesi Olarak Açma (Alternatif)

Eğer Package.swift doğrudan açılmazsa:

1. Xcode → File → New → Project → iOS App
2. Product Name: `VoiceDictation`
3. `VoiceDictation/` klasöründeki Swift dosyalarını projeye sürükle
4. Project → Package Dependencies → "+" → `https://github.com/argmaxinc/WhisperKit.git` ekle (version: 0.9.0+)
5. Target → Info → `NSMicrophoneUsageDescription` ekle

### 3. Çalıştırma

1. iPhone'u Mac'e bağla (veya Apple Developer hesabı ile wireless debug)
2. Xcode'da hedef cihazı seç
3. Cmd+R ile çalıştır
4. İlk açılışta model indirilecek (~75MB, `whisper-base`)
5. Mikrofon butonuna bas → konuş → tekrar bas → metin panoya kopyalanır

## Mimari

```
VoiceDictationApp.swift   — @main giriş noktası
ContentView.swift         — Tek ekran UI (SwiftUI)
AudioRecorder.swift       — AVAudioEngine ile 16kHz PCM kayıt
TranscriptionEngine.swift — WhisperKit ile lokal transkripsiyon
```

## Özellikler

- Lokal Whisper modeli (internet gerekmez, ilk indirmeden sonra)
- Türkçe dil desteği (varsayılan)
- Otomatik clipboard kopyalama
- Minimal UI: tek buton ile kayıt başlat/durdur

## Notlar

- İlk çalıştırmada model indirme süresi internet hızına bağlıdır
- Daha iyi sonuçlar için `whisper-base` yerine `whisper-small` kullanılabilir (`TranscriptionEngine.swift` içinde model adını değiştir)
- Simulator'da mikrofon çalışmaz, gerçek cihaz gerekir
