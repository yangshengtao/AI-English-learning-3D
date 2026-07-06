# Mobile MVP (React Native + Expo)

## Key modules
- `src/screens/SessionScreen.tsx`: session UI, websocket control, transcript/feedback rendering.
- `src/services/realtimeClient.ts`: websocket client wrapper.
- `src/services/audioService.ts`: microphone permission, recording, and playback helpers.
- `src/components/AvatarPanel.tsx`: WebView container for digital human avatar page.

## iOS first setup
1. `cd mobile`
2. `npm install`
3. `npx expo prebuild -p ios`
4. `npx expo run:ios`

## Required dependencies
- `react-native-webview`
- `expo-av`
- `expo-file-system`
- `expo-speech`

## Notes
- Current screen supports real iOS recording and sends base64 chunks to backend.
- If backend audio fails to decode, app falls back to local iOS speech (`en-US`) so conversation remains usable.
- For physical iPhone testing, replace `ws://127.0.0.1:8000` with your laptop LAN IP.
