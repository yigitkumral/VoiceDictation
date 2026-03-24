import SwiftUI

struct ContentView: View {
    @StateObject private var recorder = AudioRecorder()
    @StateObject private var engine = TranscriptionEngine()

    @State private var transcribedText = ""
    @State private var statusMessage = ""
    @State private var showPermissionAlert = false

    var body: some View {
        VStack(spacing: 24) {
            Text("VoiceDictation")
                .font(.largeTitle.bold())

            // Durum göstergesi
            HStack(spacing: 8) {
                Circle()
                    .fill(statusColor)
                    .frame(width: 12, height: 12)
                Text(statusText)
                    .foregroundStyle(.secondary)
            }

            // Ana kayıt butonu
            Button(action: toggleRecording) {
                ZStack {
                    Circle()
                        .fill(recorder.isRecording ? Color.red : Color.blue)
                        .frame(width: 80, height: 80)

                    if engine.isTranscribing {
                        ProgressView()
                            .tint(.white)
                    } else {
                        Image(systemName: recorder.isRecording ? "stop.fill" : "mic.fill")
                            .font(.system(size: 30))
                            .foregroundStyle(.white)
                    }
                }
            }
            .disabled(!engine.isModelLoaded || engine.isTranscribing)

            // Transkripsiyon sonucu
            if !transcribedText.isEmpty {
                VStack(spacing: 12) {
                    Text(transcribedText)
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .background(.ultraThinMaterial)
                        .clipShape(RoundedRectangle(cornerRadius: 12))

                    Button {
                        UIPasteboard.general.string = transcribedText
                        statusMessage = "Panoya kopyalandı!"
                        DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                            statusMessage = ""
                        }
                    } label: {
                        Label("Kopyala", systemImage: "doc.on.doc")
                    }
                    .buttonStyle(.bordered)
                }
            }

            if !statusMessage.isEmpty {
                Text(statusMessage)
                    .font(.caption)
                    .foregroundStyle(.green)
            }

            Spacer()
        }
        .padding()
        .task {
            await engine.loadModel()
        }
        .alert("Mikrofon İzni Gerekli", isPresented: $showPermissionAlert) {
            Button("Ayarlar") {
                if let url = URL(string: UIApplication.openSettingsURLString) {
                    UIApplication.shared.open(url)
                }
            }
            Button("İptal", role: .cancel) {}
        } message: {
            Text("Ses kaydı için mikrofon erişimine izin vermeniz gerekiyor.")
        }
    }

    private var statusColor: Color {
        if engine.isTranscribing { return .yellow }
        if recorder.isRecording { return .red }
        if engine.isModelLoaded { return .green }
        return .gray
    }

    private var statusText: String {
        if engine.isTranscribing { return "İşleniyor..." }
        if recorder.isRecording { return "Kayıt yapılıyor..." }
        if !engine.isModelLoaded { return engine.loadingStatus }
        return "Hazır"
    }

    private func toggleRecording() {
        if recorder.isRecording {
            // Kaydı durdur ve transkribe et
            let samples = recorder.stopRecording()
            guard !samples.isEmpty else {
                statusMessage = "Ses algılanamadı"
                return
            }

            Task {
                if let text = await engine.transcribe(audioSamples: samples), !text.isEmpty {
                    transcribedText = text
                    // Otomatik olarak panoya kopyala
                    UIPasteboard.general.string = text
                    statusMessage = "Panoya kopyalandı!"
                    DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                        statusMessage = ""
                    }
                } else {
                    statusMessage = "Metin çevrilemedi"
                }
            }
        } else {
            // Kaydı başlat
            recorder.requestPermission { granted in
                if granted {
                    do {
                        try recorder.startRecording()
                        transcribedText = ""
                        statusMessage = ""
                    } catch {
                        statusMessage = "Kayıt başlatılamadı: \(error.localizedDescription)"
                    }
                } else {
                    showPermissionAlert = true
                }
            }
        }
    }
}

#Preview {
    ContentView()
}
