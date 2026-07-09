import Constants from "expo-constants";

type AppExtra = {
  backendHttpUrl?: string;
  backendWsUrl?: string;
};

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
  const host = pickHostFromConstants() ?? "your-mac-ip";
  const httpFromEnv = extra.backendHttpUrl?.trim();
  const wsFromEnv = extra.backendWsUrl?.trim();

  const httpUrl =
    httpFromEnv && !isLocalhostUrl(httpFromEnv)
      ? httpFromEnv
      : `http://${host}:8000`;
  const wsUrl =
    wsFromEnv && !isLocalhostUrl(wsFromEnv)
      ? wsFromEnv
      : `ws://${host}:8000/v1/realtime/session`;

  return { httpUrl, wsUrl, host };
}
