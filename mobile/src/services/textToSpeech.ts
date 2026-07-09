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
  Speech.speak(trimmed, {
    language: "en-US",
    onStart: callbacks?.onStart,
    onDone: callbacks?.onDone,
    onStopped: callbacks?.onDone,
    onError: callbacks?.onError,
  });
}

export function stopSpeaking(): void {
  Speech.stop();
}
