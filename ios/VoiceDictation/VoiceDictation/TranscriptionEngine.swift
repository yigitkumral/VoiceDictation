import Foundation
import WhisperKit

/// WhisperKit ile lokal transkripsiyon motoru.
final class TranscriptionEngine: ObservableObject {
    @Published var isModelLoaded = false
    @Published var isTranscribing = false
    @Published var loadingStatus = "Model yükleniyor..."

    private var whisperKit: WhisperKit?

    /// Whisper modelini indir ve yükle.
    func loadModel() async {
        await MainActor.run {
            loadingStatus = "Model indiriliyor..."
        }

        do {
            let config = WhisperKitConfig(
                model: "openai_whisper-base",
                verbose: false,
                prewarm: true
            )
            let kit = try await WhisperKit(config)
            whisperKit = kit

            await MainActor.run {
                isModelLoaded = true
                loadingStatus = "Hazır"
            }
        } catch {
            await MainActor.run {
                loadingStatus = "Model yüklenemedi: \(error.localizedDescription)"
            }
        }
    }

    /// Float PCM verisini metne çevir.
    func transcribe(audioSamples: [Float]) async -> String? {
        guard let whisperKit else { return nil }

        await MainActor.run {
            isTranscribing = true
        }

        defer {
            Task { @MainActor in
                isTranscribing = false
            }
        }

        do {
            let results = try await whisperKit.transcribe(
                audioArray: audioSamples,
                decodeOptions: DecodingOptions(
                    language: "tr"
                )
            )
            return results.map { $0.text }.joined(separator: " ").trimmingCharacters(in: .whitespaces)
        } catch {
            print("Transkripsiyon hatası: \(error)")
            return nil
        }
    }
}
