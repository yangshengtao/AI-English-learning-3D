import Constants from "expo-constants";

type AppExtra = {
  backendHttpUrl?: string;
  backendWsUrl?: string;
};

// Deployed backend (Tencent Cloud). This is the default so the app works out of
// the box without needing a Mac running the backend locally. Override via
// EXPO_PUBLIC_BACKEND_HTTP_URL / EXPO_PUBLIC_BACKEND_WS_URL (see mobile/.env.example)
// or by editing the Backend URL fields directly in the running app if you want to
// point at a local backend instead.
const DEFAULT_BACKEND_HOST = "152.136.254.150";
const DEFAULT_BACKEND_PORT = 8000;
const DEFAULT_BACKEND_HTTP_URL = `http://${DEFAULT_BACKEND_HOST}:${DEFAULT_BACKEND_PORT}`;
const DEFAULT_BACKEND_WS_URL = `ws://${DEFAULT_BACKEND_HOST}:${DEFAULT_BACKEND_PORT}/v1/realtime/session`;

function isLocalhostUrl(url: string): boolean {
  return /localhost|127\.0\.0\.1/i.test(url);
}

function pickHostFromConstants(): string | null {
  const candidates = [
    Constants.expoConfig?.hostUri,
    Constants.expoGoConfig?.debuggerHost,
    // Legacy manifest fields still seen in some Expo Go builds.
    (Constants.manifest as { debuggerHost?: string } | null)?.debuggerHost,
  ];

  for (const candidate of candidates) {
    if (!candidate) {
      continue;
    }
    const host = candidate.split(":")[0]?.trim();
    if (host && !isLocalhostUrl(host)) {
      return host;
    }
  }
  return null;
}

export function getAppExtra(): AppExtra {
  return (Constants.expoConfig?.extra ?? {}) as AppExtra;
}

export function getLanIpHint(): string {
  return pickHostFromConstants() ?? "your-mac-ip";
}

export function resolveBackendUrls(extra: AppExtra = getAppExtra()) {
  const httpFromEnv = extra.backendHttpUrl?.trim();
  const wsFromEnv = extra.backendWsUrl?.trim();

  const httpUrl =
    httpFromEnv && !isLocalhostUrl(httpFromEnv) ? httpFromEnv : DEFAULT_BACKEND_HTTP_URL;
  const wsUrl = wsFromEnv && !isLocalhostUrl(wsFromEnv) ? wsFromEnv : DEFAULT_BACKEND_WS_URL;

  return { httpUrl, wsUrl, host: DEFAULT_BACKEND_HOST };
}
