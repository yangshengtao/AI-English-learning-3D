export type RealtimeEvent = {
  type: string;
  sessionId: string;
  traceId: string;
  timestampMs: number;
  payload: Record<string, unknown>;
};

type RealtimeCallbacks = {
  onOpen?: () => void;
  onMessage: (event: RealtimeEvent) => void;
  onError?: (error: string) => void;
  onClose?: () => void;
};

export class RealtimeClient {
  private ws: WebSocket | null = null;

  connect(url: string, token: string, callbacks: RealtimeCallbacks) {
    const urlWithToken = `${url}?token=${encodeURIComponent(token)}`;
    this.ws = new WebSocket(urlWithToken);

    this.ws.onopen = () => {
      callbacks.onOpen?.();
    };

    this.ws.onmessage = (message) => {
      try {
        callbacks.onMessage(JSON.parse(message.data) as RealtimeEvent);
      } catch (error) {
        callbacks.onError?.(`Failed to parse event: ${String(error)}`);
      }
    };

    this.ws.onerror = () => {
      callbacks.onError?.("Realtime socket error.");
    };

    this.ws.onclose = () => {
      callbacks.onClose?.();
    };
  }

  send(event: RealtimeEvent) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      return;
    }
    this.ws.send(JSON.stringify(event));
  }

  disconnect() {
    this.ws?.close();
    this.ws = null;
  }
}
