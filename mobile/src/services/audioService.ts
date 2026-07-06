import { Audio, InterruptionModeIOS } from "expo-av";
import * as FileSystem from "expo-file-system";
import * as Speech from "expo-speech";

type RecorderState = {
  recording: Audio.Recording | null;
};

const recorderState: RecorderState = {
  recording: null,
};

export async function prepareAudioSession(): Promise<void> {
  await Audio.setAudioModeAsync({
    allowsRecordingIOS: true,
    interruptionModeIOS: InterruptionModeIOS.DoNotMix,
    playsInSilentModeIOS: true,
    shouldDuckAndroid: true,
    staysActiveInBackground: false,
  });
}

export async function requestMicrophonePermission(): Promise<boolean> {
  const { granted } = await Audio.requestPermissionsAsync();
  return granted;
}

export async function startRecording(): Promise<void> {
  if (recorderState.recording) {
    return;
  }
  const recording = new Audio.Recording();
  await recording.prepareToRecordAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
  await recording.startAsync();
  recorderState.recording = recording;
}

export async function stopRecordingAndGetBase64(): Promise<string | null> {
  const recording = recorderState.recording;
  if (!recording) {
    return null;
  }
  await recording.stopAndUnloadAsync();
  recorderState.recording = null;

  const uri = recording.getURI();
  if (!uri) {
    return null;
  }

  const base64 = await FileSystem.readAsStringAsync(uri, {
    encoding: FileSystem.EncodingType.Base64,
  });
  return base64;
}

export async function playAudioFromBase64(base64: string, mimeType = "audio/wav"): Promise<boolean> {
  try {
    const dataUri = `data:${mimeType};base64,${base64}`;
    const { sound } = await Audio.Sound.createAsync({ uri: dataUri }, { shouldPlay: true });
    sound.setOnPlaybackStatusUpdate((status) => {
      if (status.isLoaded && status.didJustFinish) {
        sound.unloadAsync();
      }
    });
    return true;
  } catch {
    return false;
  }
}

export function speakFallback(text: string): void {
  if (!text.trim()) {
    return;
  }
  Speech.speak(text, {
    language: "en-US",
    rate: 0.95,
    pitch: 1.0,
  });
}
