# Mobile MVP (Expo / React Native)

Expo app for the 1v1 English tutor session. Works on iOS device (priority), Android, and simulator.

## Prerequisites

- Node.js 22+
- Backend running and reachable from your phone (`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`)
- iOS path A (fastest): [Expo Go](https://expo.dev/go) on your iPhone
- iOS path B (native build): Xcode + CocoaPods

## Install

```bash
cd mobile
npm install
```

## Run on iPhone (recommended first: Expo Go)

1. Start backend on your Mac:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

2. Find your Mac LAN IP (example: `192.168.1.23`).

3. Start Expo:

```bash
cd mobile
npm start
```

4. Open Expo Go on iPhone, scan the QR code (phone and Mac must be on the same Wi-Fi).

### Not on the same Wi-Fi as your Mac? Use tunnel mode

```bash
npm run start:tunnel
```

This routes the Metro dev server through an ngrok tunnel (`@expo/ngrok`, already a
devDependency) instead of your LAN, so the phone can be on any network (mobile data,
a different Wi-Fi, etc.) — it just can't reach `localhost`/your Mac's LAN IP directly.
Same QR code flow in Expo Go, just no Wi-Fi requirement. Notes:
- Your Mac still needs to be running `npm run start:tunnel` — this is still Expo Go dev
  mode, not a standalone install (see "Connect to a deployed backend" below for why the
  *backend* doesn't have this limitation).
- Slightly higher latency than `--lan` since traffic round-trips through ngrok's relay.
- First run may need to install `@expo/ngrok` if it's missing (`npm install`).

5. In the app:
   - Set **Backend HTTP URL** to `http://<mac-ip>:8000`
   - Set **Backend WebSocket URL** to `ws://<mac-ip>:8000/v1/realtime/session`
   - Tap **Fetch Dev Token**, then **Connect**
   - Try **Send Text** or **Mock Voice Turn**

Optional env overrides before `npm start`:

```bash
EXPO_PUBLIC_BACKEND_HTTP_URL=http://192.168.1.23:8000 \
EXPO_PUBLIC_BACKEND_WS_URL=ws://192.168.1.23:8000/v1/realtime/session \
npm start
```

## Connect to a deployed backend instead of your Mac

The app defaults to the deployed Tencent Cloud backend — `DEFAULT_BACKEND_HOST` in
`src/config.ts` is hardcoded to `152.136.254.150:8000`. `npm start` launches the app
already pointed at it, so **no local backend and no manual URL typing needed** for
day-to-day mobile testing.

- To test against your local Mac backend instead, either set
  `EXPO_PUBLIC_BACKEND_HTTP_URL` / `EXPO_PUBLIC_BACKEND_WS_URL` in a `mobile/.env`
  (see `.env.example`) to your Mac's LAN IP before `npm start`, or just overwrite the
  two fields inside the running app (they always take priority over the default).
- The remote backend currently talks over plain `http`/`ws` (no TLS) — that's fine for
  Expo Go dev testing, but a standalone/production build will need a real domain +
  HTTPS in front of it (see `docs/troubleshooting.md`).

## Run on iPhone (native dev build)

Use this when you need a standalone dev client or modules beyond Expo Go.

```bash
cd mobile
npm install
npx expo prebuild --platform ios
npx expo run:ios --device
```

Requires Apple developer signing for a physical device.

## Key modules

- `src/screens/SessionScreen.tsx`: session UI, websocket control, transcript/feedback rendering
- `src/services/realtimeClient.ts`: websocket client wrapper (header + query token auth)
- `src/services/audioPlayer.ts`: decodes `agent.audio` PCM16 payload, wraps it in a WAV
  header, and plays it via `expo-av`. Skips playback (with a status message) when the
  backend TTS provider is still a placeholder.
- `src/services/backendApi.ts`: typed REST calls to the backend (dev token, etc.)
- `src/components/AvatarPanel.tsx`: WebView container for digital human avatar page
- `app.config.ts`: bundle id, ATS local networking, default backend URLs

## Notes

- `localhost` only works on simulator; real devices must use your Mac LAN IP.
- Current screen includes text fallback and a mock voice event path for protocol validation.
- Real microphone streaming should replace `mockVoiceTurn` with `expo-av`'s `Audio.Recording` in a later iteration.
- Agent text replies now use the backend's real DeepSeek LLM (once `DEEPSEEK_API_KEY` is set); agent audio playback is wired but stays silent until a real TTS provider is connected on the backend.

## Troubleshooting

常见坑（Expo Go、localhost、HTTP 405、SDK 不匹配等）见 [`docs/troubleshooting.md`](../docs/troubleshooting.md)。
