import { StatusBar } from "expo-status-bar";
import { StyleSheet, View } from "react-native";

import { SessionScreen } from "./src/screens/SessionScreen";

export default function App() {
  return (
    <View style={styles.root}>
      <StatusBar style="light" />
      <SessionScreen />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#0b0f17",
  },
});
