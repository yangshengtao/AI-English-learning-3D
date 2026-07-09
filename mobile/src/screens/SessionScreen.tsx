import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Button,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";

import { Audio } from "expo-av";

import { AvatarPanel } from "../components/AvatarPanel";
import { playPcm16Audio } from "../services/audioPlayer";
import { requestMicrophonePermission, startRecording, stopRecording } from "../services/audioRecorder";
import { fetchDevToken } from "../services/backendApi";
import { getAppExtra, getLanIpHint, resolveBackendUrls } from "../config";
import { RealtimeClient, RealtimeEvent } from "../services/realtimeClient";
import { speakAgentReply, stopSpeaking } from "../services/textToSpeech";

const AVATAR_PAGE_URL = "https://example.com/avatar";

export function SessionScreen() {
  const extra = getAppExtra();
  const lanIpHint = getLanIpHint();
  const defaults = resolveBackendUrls(extra);
  const realtimeClient = useMemo(() => new RealtimeClient(), []);
  const traceRef = useRef(0);
  const [sessionId] = useState(`sess_${Date.now()}`);
  const [backendHttpUrl, setBackendHttpUrl] = useState(defaults.httpUrl);
  const [backendWsUrl, setBackendWsUrl] = useState(defaults.wsUrl);
  const [token, setToken] = useState("");
  const [typedText, setTypedText] = useState("");
  const [status, setStatus] = useState("disconnected");
  const [isFetchingToken, setIsFetchingToken] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [agentReply, setAgentReply] = useState("");
  const [feedback, setFeedback] = useState("");
  const [audioNote, setAudioNote] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [speechStatus, setSpeechStatus] = useState<"idle" | "speaking">("idle");
  const recordingRef = useRef<Audio.Recording | null>(null);
  // Voice turns (audio.commit) get a cloud-synthesized `agent.audio` reply right
  // after `agent.text`; text turns (session.input_text) never do. We use this to
  // avoid playing both the cloud audio *and* on-device expo-speech at once —
  // on-device speech only kicks in as a fallback when cloud audio is missing/placeholder.
  const expectAudioReplyRef = useRef(false);
  const latestAgentReplyRef = useRef("");

  useEffect(() => {
    return () => {
      realtimeClient.disconnect();
      stopSpeaking();
      if (recordingRef.current) {
        recordingRef.current.stopAndUnloadAsync().catch(() => undefined);
      }
    };
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

  const fetchToken = async () => {
    const baseUrl = backendHttpUrl.trim();
    if (!baseUrl) {
      setStatus("missing backend http url");
      return;
    }

    setIsFetchingToken(true);
    try {
      const nextToken = await fetchDevToken(baseUrl);
      setToken(nextToken);
      setStatus("token ready");
    } catch (error) {
      setStatus(`token fetch failed (${baseUrl}): ${String(error)}`);
    } finally {
      setIsFetchingToken(false);
    }
  };

  const connect = () => {
    const wsUrl = backendWsUrl.trim();
    if (!wsUrl) {
      setStatus("missing websocket url");
      return;
    }
    if (!token.trim()) {
      setStatus("missing token");
      return;
    }

    setStatus("connecting");
    realtimeClient.connect(wsUrl, token.trim(), {
      onOpen: () => {
        setStatus("connected");
        send("session.start", { mode: "free_talk" });
      },
      onMessage: (event) => {
        if (event.type === "session.ack") {
          setStatus("session ready");
        }
        if (event.type === "asr.partial" || event.type === "asr.final") {
          setTranscript(String(event.payload.text ?? ""));
        }
        if (event.type === "agent.text") {
          const text = String(event.payload.text ?? "");
          setAgentReply(text);
          latestAgentReplyRef.current = text;
          // Voice turns: hold off — `agent.audio` (cloud TTS) arrives next and
          // takes priority. Text turns: no `agent.audio` is coming, speak now.
          if (!expectAudioReplyRef.current) {
            speakAgentReply(text, {
              onStart: () => setSpeechStatus("speaking"),
              onDone: () => setSpeechStatus("idle"),
              onError: () => setSpeechStatus("idle"),
            });
          }
        }
        if (event.type === "agent.audio") {
          const wasExpectingAudio = expectAudioReplyRef.current;
          expectAudioReplyRef.current = false;
          const audioBase64 = String(event.payload.audioBase64 ?? "");
          const sampleRate = Number(event.payload.sampleRate ?? 24000);
          playPcm16Audio(audioBase64, sampleRate)
            .then((result) => {
              setAudioNote(result.played ? "playing agent audio" : (result.reason ?? "audio not played"));
              // Cloud TTS wasn't available (placeholder/unconfigured/error) —
              // fall back to on-device speech so the voice turn isn't silent.
              if (!result.played && wasExpectingAudio && latestAgentReplyRef.current) {
                speakAgentReply(latestAgentReplyRef.current, {
                  onStart: () => setSpeechStatus("speaking"),
                  onDone: () => setSpeechStatus("idle"),
                  onError: () => setSpeechStatus("idle"),
                });
              }
            })
            .catch((error) => setAudioNote(`audio playback error: ${String(error)}`));
        }
        if (event.type === "eval.feedback") {
          const score = Number(event.payload.pronunciationScore ?? 0);
          const tips = (event.payload.tips as string[] | undefined) ?? [];
          setFeedback(`Score: ${score} | Tip: ${tips[0] ?? ""}`);
        }
        if (event.type === "error") {
          setStatus(`error: ${String(event.payload.message ?? "unknown")}`);
        }
      },
      onError: (error) => setStatus(`error: ${error}`),
      onClose: () => setStatus("closed"),
    });
  };

  const replayAgentReply = () => {
    if (!agentReply.trim()) {
      return;
    }
    speakAgentReply(agentReply, {
      onStart: () => setSpeechStatus("speaking"),
      onDone: () => setSpeechStatus("idle"),
      onError: () => setSpeechStatus("idle"),
    });
  };

  const submitText = () => {
    if (!typedText.trim()) {
      return;
    }
    expectAudioReplyRef.current = false;
    send("session.input_text", { text: typedText.trim() });
    setTypedText("");
  };

  const toggleRecording = async () => {
    if (isRecording) {
      const recording = recordingRef.current;
      recordingRef.current = null;
      setIsRecording(false);
      if (!recording) {
        return;
      }
      try {
        setStatus("processing recording...");
        const { base64, format, sampleRate } = await stopRecording(recording);
        expectAudioReplyRef.current = true;
        send("audio.chunk", { seq: 1, audioBase64: base64, sampleRate, format });
        send("audio.commit", { lastSeq: 1 });
        setStatus("recording sent");
      } catch (error) {
        setStatus(`recording error: ${String(error)}`);
      }
      return;
    }

    try {
      const granted = await requestMicrophonePermission();
      if (!granted) {
        setStatus("microphone permission denied");
        return;
      }
      const recording = await startRecording();
      recordingRef.current = recording;
      setIsRecording(true);
      setStatus("recording...");
    } catch (error) {
      setStatus(`recording start failed: ${String(error)}`);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>1v1 English Tutor Session</Text>
        <Text style={styles.hint}>
          Defaults to the deployed backend. To test against your Mac instead, replace the
          URLs below with your Mac LAN IP (detected: {lanIpHint}), not localhost.
        </Text>
        <AvatarPanel avatarPageUrl={AVATAR_PAGE_URL} />

        <Text style={styles.label}>Backend HTTP URL</Text>
        <TextInput
          value={backendHttpUrl}
          onChangeText={setBackendHttpUrl}
          style={styles.input}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <Text style={styles.label}>Backend WebSocket URL</Text>
        <TextInput
          value={backendWsUrl}
          onChangeText={setBackendWsUrl}
          style={styles.input}
          autoCapitalize="none"
          autoCorrect={false}
        />

        <Text style={styles.label}>JWT Token</Text>
        <TextInput
          value={token}
          onChangeText={setToken}
          style={styles.input}
          placeholder="Paste token or fetch below"
          autoCapitalize="none"
          autoCorrect={false}
        />

        <View style={styles.row}>
          <Button
            title={isFetchingToken ? "Fetching..." : "Fetch Dev Token"}
            onPress={fetchToken}
            disabled={isFetchingToken}
          />
          <Button title="Connect" onPress={connect} />
        </View>
        {isFetchingToken ? <ActivityIndicator color="#7bd88f" /> : null}

        <View style={styles.row}>
          <Button
            title={isRecording ? "⏹ Stop & Send" : "🎙 Start Recording"}
            onPress={toggleRecording}
            color={isRecording ? "#e05555" : undefined}
          />
        </View>

        <Text style={styles.label}>Text Fallback</Text>
        <TextInput
          value={typedText}
          onChangeText={setTypedText}
          style={styles.input}
          placeholder="Type your sentence"
        />
        <Button title="Send Text" onPress={submitText} />

        <View style={styles.row}>
          <Button title="🔊 Replay Agent Reply" onPress={replayAgentReply} />
        </View>

        <Text style={styles.status}>Status: {status}</Text>
        <Text style={styles.block}>Transcript: {transcript || "-"}</Text>
        <Text style={styles.block}>Agent: {agentReply || "-"}</Text>
        <Text style={styles.block}>Agent audio: {audioNote || "-"}</Text>
        <Text style={styles.block}>Voice: {speechStatus}</Text>
        <Text style={styles.block}>Feedback: {feedback || "-"}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#0b0f17" },
  container: { gap: 12, padding: 16, paddingBottom: 32 },
  title: { fontSize: 22, fontWeight: "700", color: "white" },
  hint: { fontSize: 12, color: "#7a8ea8", lineHeight: 18 },
  label: { fontSize: 14, color: "#a3b1c2" },
  input: {
    borderColor: "#2d3a4d",
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    color: "white",
  },
  row: { flexDirection: "row", justifyContent: "space-between", gap: 12 },
  status: { color: "#7bd88f", marginTop: 8 },
  block: { color: "white" },
});
