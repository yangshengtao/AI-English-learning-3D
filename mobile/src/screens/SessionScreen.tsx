import React, { useEffect, useMemo, useRef, useState } from "react";
import { Button, SafeAreaView, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";

import { AvatarPanel } from "../components/AvatarPanel";
import { RealtimeClient, RealtimeEvent } from "../services/realtimeClient";

const BACKEND_WS_URL = "ws://localhost:8000/v1/realtime/session";
const AVATAR_PAGE_URL = "https://example.com/avatar";

export function SessionScreen() {
  const realtimeClient = useMemo(() => new RealtimeClient(), []);
  const traceRef = useRef(0);
  const [sessionId] = useState(`sess_${Date.now()}`);
  const [token, setToken] = useState("");
  const [typedText, setTypedText] = useState("");
  const [status, setStatus] = useState("disconnected");
  const [transcript, setTranscript] = useState("");
  const [agentReply, setAgentReply] = useState("");
  const [feedback, setFeedback] = useState("");

  useEffect(() => {
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
      onMessage: (event) => {
        if (event.type === "asr.partial" || event.type === "asr.final") {
          setTranscript(String(event.payload.text ?? ""));
        }
        if (event.type === "agent.text") {
          setAgentReply(String(event.payload.text ?? ""));
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
    setStatus("connected");
    send("session.start", { mode: "free_talk" });
  };

  const submitText = () => {
    if (!typedText.trim()) {
      return;
    }
    send("session.input_text", { text: typedText.trim() });
    setTypedText("");
  };

  const mockVoiceTurn = () => {
    // RN audio capture should be added with react-native-audio-recorder-player or Expo AV.
    send("audio.chunk", { seq: 1, audioBase64: "ZmFrZV9jaHVuaw==", sampleRate: 16000, format: "pcm16" });
    send("audio.commit", { lastSeq: 1 });
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
          <Button title="Mock Voice Turn" onPress={mockVoiceTurn} />
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
