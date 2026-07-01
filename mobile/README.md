# Mobile MVP (React Native)

## Key modules
- `src/screens/SessionScreen.tsx`: session UI, websocket control, transcript/feedback rendering.
- `src/services/realtimeClient.ts`: websocket client wrapper.
- `src/components/AvatarPanel.tsx`: WebView container for digital human avatar page.

## Required dependencies
- `react-native-webview`
- audio capture package (pick one): `react-native-audio-recorder-player` or Expo AV

## Notes
- Current screen includes text fallback and a mock voice event path to validate end-to-end protocol quickly.
- Real microphone streaming should replace `mockVoiceTurn` for production use.
