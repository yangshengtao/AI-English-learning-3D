import { Audio } from "expo-av";
import * as Speech from "expo-speech";

export type SpeakCallbacks = {
  onStart?: () => void;
  onDone?: () => void;
  onError?: (error: unknown) => void;
};

export function speakAgentReply(text: string, callbacks?: SpeakCallbacks): void {
  const trimmed = text.trim();
  if (!trimmed) {
    return;
  }

  Speech.stop();
  // expo-speech shares the same iOS AVAudioSession as expo-av, so it is
  // subject to the same earpiece-routing bug after a recording session (see
  // audioPlayer.ts). Reset the session to playback-only right before
  // speaking or this can come out barely audible too.
  Audio.setAudioModeAsync({
    allowsRecordingIOS: false,
    playsInSilentModeIOS: true,
    staysActiveInBackground: false,
  })
    .catch(() => undefined)
    .finally(() => {
      Speech.speak(trimmed, {
        language: "en-US",
        onStart: callbacks?.onStart,
        onDone: callbacks?.onDone,
        onStopped: callbacks?.onDone,
        onError: callbacks?.onError,
      });
    });
}

export function stopSpeaking(): void {
  Speech.stop();
}
