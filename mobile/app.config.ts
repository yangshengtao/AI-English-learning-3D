const config = {
  name: "English Tutor",
  slug: "english-tutor",
  version: "1.0.0",
  orientation: "portrait",
  icon: "./assets/icon.png",
  userInterfaceStyle: "dark",
  splash: {
    image: "./assets/splash-icon.png",
    resizeMode: "contain",
    backgroundColor: "#0b0f17",
  },
  ios: {
    supportsTablet: true,
    bundleIdentifier: "com.aienglish.tutor",
    infoPlist: {
      NSAppTransportSecurity: {
        NSAllowsLocalNetworking: true,
      },
      NSMicrophoneUsageDescription:
        "Microphone access is used for speaking practice with your AI tutor.",
    },
  },
  android: {
    adaptiveIcon: {
      foregroundImage: "./assets/adaptive-icon.png",
      backgroundColor: "#0b0f17",
    },
    package: "com.aienglish.tutor",
    permissions: ["RECORD_AUDIO"],
  },
  web: {
    favicon: "./assets/favicon.png",
  },
  extra: {
    backendHttpUrl: process.env.EXPO_PUBLIC_BACKEND_HTTP_URL,
    backendWsUrl: process.env.EXPO_PUBLIC_BACKEND_WS_URL,
  },
};

export default config;