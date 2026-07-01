import React from "react";
import { StyleSheet, View } from "react-native";
import { WebView } from "react-native-webview";

type AvatarPanelProps = {
  avatarPageUrl: string;
};

export function AvatarPanel({ avatarPageUrl }: AvatarPanelProps) {
  return (
    <View style={styles.container}>
      <WebView source={{ uri: avatarPageUrl }} javaScriptEnabled allowsInlineMediaPlayback />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    height: 260,
    borderRadius: 12,
    overflow: "hidden",
    backgroundColor: "#101520",
  },
});
