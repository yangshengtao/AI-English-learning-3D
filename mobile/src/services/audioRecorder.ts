import { Platform } from "react-native";
import { Audio } from "expo-av";
import * as FileSystem from "expo-file-system/legacy";

export type RecordedAudio = {
  base64: string;
  format: string;
  sampleRate: number;
};

// Mono 16kHz — the lowest common denominator that both cloud ASR providers
// accept: Deepgram nova-3 handles it natively, and Alibaba Cloud NLS
// one-sentence recognition *only* accepts mono audio at 8000/16000 Hz.
const RECORDING_SAMPLE_RATE = 16000;

// iOS's AVAudioRecorder can fail to prepare with a compressed format (AAC) at
// this mono/low sample rate combination — throws "Prepare encountered an
// error: recorder not prepared" (see https://github.com/expo/expo/issues/15818).
// Uncompressed Linear PCM in a WAV container is the combination that reliably
// prepares, and both Deepgram and Alibaba Cloud NLS accept WAV directly.
const IOS_RECORDING_OPTIONS: Audio.RecordingOptionsIOS = {
  extension: ".wav",
  outputFormat: Audio.IOSOutputFormat.LINEARPCM,
  audioQuality: Audio.IOSAudioQuality.MAX,
  sampleRate: RECORDING_SAMPLE_RATE,
  numberOfChannels: 1,
  bitRate: RECORDING_SAMPLE_RATE * 16,
  linearPCMBitDepth: 16,
  linearPCMIsBigEndian: false,
  linearPCMIsFloat: false,
};

// Android's MediaRecorder has no raw PCM/WAV output option, so we keep the
// standard AAC-in-MPEG4 container here; both ASR providers accept "m4a"/"aac".
const ANDROID_RECORDING_OPTIONS: Audio.RecordingOptionsAndroid = {
  extension: ".m4a",
  outputFormat: Audio.AndroidOutputFormat.MPEG_4,
  audioEncoder: Audio.AndroidAudioEncoder.AAC,
  sampleRate: RECORDING_SAMPLE_RATE,
  numberOfChannels: 1,
  bitRate: 64000,
};

const RECORDING_OPTIONS: Audio.RecordingOptions = {
  isMeteringEnabled: false,
  android: ANDROID_RECORDING_OPTIONS,
  ios: IOS_RECORDING_OPTIONS,
  web: {
    mimeType: "audio/webm",
    bitsPerSecond: 64000,
  },
};

// Must match the `extension`/`outputFormat` picked per-platform above.
const RECORDING_FORMAT = Platform.OS === "ios" ? "wav" : "m4a";

export async function requestMicrophonePermission(): Promise<boolean> {
  const { status } = await Audio.requestPermissionsAsync();
  return status === "granted";
}

export async function startRecording(): Promise<Audio.Recording> {
  await Audio.setAudioModeAsync({
    allowsRecordingIOS: true,
    playsInSilentModeIOS: true,
  });

  const { recording } = await Audio.Recording.createAsync(RECORDING_OPTIONS);
  return recording;
}

export async function stopRecording(recording: Audio.Recording): Promise<RecordedAudio> {
  await recording.stopAndUnloadAsync();
  // Belt-and-suspenders reset — the authoritative reset that actually fixes
  // iOS earpiece-routing lives right before playback (see audioPlayer.ts /
  // textToSpeech.ts), but flipping this back immediately here too avoids a
  // window where some other code could play audio before that point.
  await Audio.setAudioModeAsync({ allowsRecordingIOS: false, playsInSilentModeIOS: true });

  const uri = recording.getURI();
  if (!uri) {
    throw new Error("recording produced no file URI");
  }

  const base64 = await FileSystem.readAsStringAsync(uri, {
    encoding: FileSystem.EncodingType.Base64,
  });

  return { base64, format: RECORDING_FORMAT, sampleRate: RECORDING_SAMPLE_RATE };
}
