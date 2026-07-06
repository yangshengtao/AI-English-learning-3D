import React, { useEffect, useMemo, useRef, useState } from "react";
import { Button, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { AvatarPanel } from "../components/AvatarPanel";
import {
  playAudioFromBase64,
  prepareAudioSession,
  requestMicrophonePermission,
  speakFallback,
  startRecording,
  stopRecordingAndGetBase64,
} from "../services/audioService";
import { RealtimeClient, RealtimeEvent } from "../services/realtimeClient";

const BACKEND_WS_URL = "ws://127.0.0.1:8000/v1/realtime/session";
const AVATAR_PAGE_URL = "https://example.com/avatar";

export function SessionScreen() {
  const realtimeClient = useMemo(() => new RealtimeClient(), []);
  const traceRef = useRef(0);
  const [sessionId] = useState(`sess_${Date.now()}`);
  const [token, setToken] = useState("");
  const [typedText, setTypedText] = useState("");
  const [status, setStatus] = useState("disconnected");
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [agentReply, setAgentReply] = useState("");
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
    prepareAudioSession().catch(() => setStatus("audio session setup failed"));
    return () => realtimeClient.disconnect();
  }, [realtimeClient]);

  const nextTraceId = () => {
    traceRef.current += 1;
    return `trace_${traceRef.current}`;
  };

  const send = (type: string, payload: Record<string, unknown>) => {
    const event: RealtimeEvent = {
      type,
      sessionId,
      traceId: nextTraceId(),
      timestampMs: Date.now(),
      payload,
    };
    realtimeClient.send(event);
  };

  const connect = () => {
    if (!token.trim()) {
      setStatus("missing token");
      return;
    }
    realtimeClient.connect(BACKEND_WS_URL, token.trim(), {
      onOpen: () => {
        setStatus("connected");
        send("session.start", { mode: "free_talk" });
      },
      onMessage: (event) => {
        if (event.type === "asr.partial" || event.type === "asr.final") {
          setTranscript(String(event.payload.text ?? ""));
        }
        if (event.type === "agent.text") {
          const text = String(event.payload.text ?? "");
          setAgentReply(text);
          speakFallback(text);
        }
        if (event.type === "agent.audio") {
          const base64 = String(event.payload.audioBase64 ?? "");
          const mimeType = String(event.payload.mimeType ?? "audio/wav");
          playAudioFromBase64(base64, mimeType).catch(() => {
            // Keep UI flow resilient even when backend audio format mismatches.
          });
        }
        if (event.type === "eval.feedback") {
          const score = Number(event.payload.pronunciationScore ?? 0);
          const tips = (event.payload.tips as string[] | undefined) ?? [];
          setFeedback(`Score: ${score} | Tip: ${tips[0] ?? ""}`);
        }
      },
      onError: (error) => setStatus(`error: ${error}`),
      onClose: () => setStatus("closed"),
    });
    setStatus("connecting");
  };

  const submitText = () => {
    if (!typedText.trim()) {
      return;
    }
    send("session.input_text", { text: typedText.trim() });
    setTypedText("");
  };

  const startVoiceInput = async () => {
    const granted = await requestMicrophonePermission();
    if (!granted) {
      setStatus("microphone permission denied");
      return;
    }
    try {
      await startRecording();
      setIsRecording(true);
      setStatus("recording");
    } catch (error) {
      setStatus(`recording start failed: ${String(error)}`);
    }
  };

  const stopVoiceInput = async () => {
    try {
      const audioBase64 = await stopRecordingAndGetBase64();
      setIsRecording(false);
      if (!audioBase64) {
        setStatus("recording empty");
        return;
      }
      send("audio.chunk", {
        seq: 1,
        audioBase64,
        sampleRate: 44100,
        format: "m4a",
      });
      send("audio.commit", { lastSeq: 1 });
      setStatus("voice turn sent");
    } catch (error) {
      setIsRecording(false);
      setStatus(`recording stop failed: ${String(error)}`);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>1v1 English Tutor Session</Text>
        <AvatarPanel avatarPageUrl={AVATAR_PAGE_URL} />

        <Text style={styles.label}>JWT Token</Text>
        <TextInput value={token} onChangeText={setToken} style={styles.input} placeholder="Paste token here" />
        <View style={styles.row}>
          <Button title="Connect" onPress={connect} />
          <Button title={isRecording ? "Stop Recording" : "Start Recording"} onPress={isRecording ? stopVoiceInput : startVoiceInput} />
        </View>

        <Text style={styles.label}>Text Fallback</Text>
        <TextInput
          value={typedText}
          onChangeText={setTypedText}
          style={styles.input}
          placeholder="Type your sentence"
        />
        <Button title="Send Text" onPress={submitText} />

        <Text style={styles.status}>Status: {status}</Text>
        <Text style={styles.block}>Transcript: {transcript || "-"}</Text>
        <Text style={styles.block}>Agent: {agentReply || "-"}</Text>
        <Text style={styles.block}>Feedback: {feedback || "-"}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0b0f17" },
  container: { gap: 12, padding: 16 },
  title: { fontSize: 22, fontWeight: "700", color: "white" },
  label: { fontSize: 14, color: "#a3b1c2" },
  input: {
    borderColor: "#2d3a4d",
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    color: "white",
  },
  row: { flexDirection: "row", justifyContent: "space-between" },
  status: { color: "#7bd88f", marginTop: 8 },
  block: { color: "white" },
});
