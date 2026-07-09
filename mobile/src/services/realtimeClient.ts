export type RealtimeEvent = {
  type: string;
  sessionId: string;
  traceId: string;
  timestampMs: number;
  payload: Record<string, unknown>;
};

type RealtimeCallbacks = {
  onMessage: (event: RealtimeEvent) => void;
  onError?: (error: string) => void;
  onClose?: () => void;
  onOpen?: () => void;
};

type NativeWebSocketCtor = {
  new (
    url: string,
    protocols?: string | string[] | null,
    options?: { headers?: Record<string, string> },
  ): WebSocket;
};

const NativeWebSocket = WebSocket as unknown as NativeWebSocketCtor;

function withTokenQuery(url: string, token: string): string {
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}token=${encodeURIComponent(token)}`;
}

export class RealtimeClient {
  private ws: WebSocket | null = null;

  connect(url: string, token: string, callbacks: RealtimeCallbacks) {
    this.disconnect();

    const trimmedToken = token.trim();
    const wsUrl = withTokenQuery(url, trimmedToken);

    this.ws = new NativeWebSocket(wsUrl, undefined, {
      headers: {
        Authorization: `Bearer ${trimmedToken}`,
      },
    });

    this.ws.onopen = () => {
      callbacks.onOpen?.();
    };

    this.ws.onmessage = (message) => {
      try {
        callbacks.onMessage(JSON.parse(String(message.data)) as RealtimeEvent);
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
