import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system/legacy";
import * as base64js from "base64-js";

// Placeholder/error TTS providers (see backend/app/providers/tts_provider.py)
// return plain-text bytes tagged with these prefixes instead of real PCM
// audio. We detect and skip playback so users don't hear meaningless static
// when a provider isn't configured or a request fails.
const PLACEHOLDER_MARKERS = [
  "ELEVENLABS_AUDIO::",
  "AZURE_AUDIO::",
  "DEEPGRAM_TTS_PLACEHOLDER::",
  "DEEPGRAM_TTS_ERROR::",
];

export type PlaybackResult = {
  played: boolean;
  reason?: string;
};

let currentSound: Audio.Sound | null = null;

function bytesStartWith(bytes: Uint8Array, marker: string): boolean {
  if (bytes.length < marker.length) {
    return false;
  }
  for (let i = 0; i < marker.length; i += 1) {
    if (bytes[i] !== marker.charCodeAt(i)) {
      return false;
    }
  }
  return true;
}

function isPlaceholderAudio(bytes: Uint8Array): boolean {
  return PLACEHOLDER_MARKERS.some((marker) => bytesStartWith(bytes, marker));
}

function buildWavHeader(
  pcmLength: number,
  sampleRate: number,
  channels = 1,
  bitsPerSample = 16,
): Uint8Array {
  const blockAlign = (channels * bitsPerSample) / 8;
  const byteRate = sampleRate * blockAlign;
  const header = new Uint8Array(44);
  const view = new DataView(header.buffer);

  const writeString = (offset: number, text: string) => {
    for (let i = 0; i < text.length; i += 1) {
      view.setUint8(offset + i, text.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + pcmLength, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, channels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(36, "data");
  view.setUint32(40, pcmLength, true);

  return header;
}

async function unloadCurrentSound() {
  if (currentSound) {
    try {
      await currentSound.unloadAsync();
    } catch {
      // ignore unload errors from an already-released sound
    }
    currentSound = null;
  }
}

export async function playPcm16Audio(
  audioBase64: string,
  sampleRate: number,
): Promise<PlaybackResult> {
  if (!audioBase64) {
    return { played: false, reason: "empty audio payload" };
  }

  let pcmBytes: Uint8Array;
  try {
    pcmBytes = base64js.toByteArray(audioBase64);
  } catch (error) {
    return { played: false, reason: `invalid base64 audio: ${String(error)}` };
  }

  if (isPlaceholderAudio(pcmBytes)) {
    return {
      played: false,
      reason: "placeholder TTS bytes — connect a real TTS provider to hear audio",
    };
  }

  try {
    const header = buildWavHeader(pcmBytes.length, sampleRate);
    const wavBytes = new Uint8Array(header.length + pcmBytes.length);
    wavBytes.set(header, 0);
    wavBytes.set(pcmBytes, header.length);
    const wavBase64 = base64js.fromByteArray(wavBytes);

    const fileUri = `${FileSystem.cacheDirectory}agent-audio-${Date.now()}.wav`;
    await FileSystem.writeAsStringAsync(fileUri, wavBase64, {
      encoding: FileSystem.EncodingType.Base64,
    });

    await unloadCurrentSound();
    // iOS pins audio output to the quiet earpiece receiver (not the main
    // speaker) after any recording session, no matter what the hardware
    // volume buttons are set to, until allowsRecordingIOS is explicitly set
    // back to false immediately before the next playback — see
    // https://github.com/expo/expo/issues/19220. Re-asserting it here (not
    // just once in stopRecording) is what actually makes it stick.
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false,
      playsInSilentModeIOS: true,
      staysActiveInBackground: false,
    });

    const { sound } = await Audio.Sound.createAsync(
      { uri: fileUri },
      { shouldPlay: true, volume: 1.0 },
    );
    currentSound = sound;
    sound.setOnPlaybackStatusUpdate((playbackStatus) => {
      if (playbackStatus.isLoaded && playbackStatus.didJustFinish) {
        sound.unloadAsync().catch(() => undefined);
      }
    });

    return { played: true };
  } catch (error) {
    return { played: false, reason: String(error) };
  }
}
