type DevTokenResponse = {
  token?: string;
};

export async function fetchDevToken(baseUrl: string, userId = "demo-user"): Promise<string> {
  const normalized = baseUrl.trim().replace(/\/$/, "");
  if (!normalized) {
    throw new Error("backend HTTP URL is empty");
  }

  const response = await fetch(`${normalized}/v1/auth/dev-token?user_id=${encodeURIComponent(userId)}`, {
    method: "POST",
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }

  const data = (await response.json()) as DevTokenResponse;
  if (!data.token) {
    throw new Error("token missing in response");
  }

  return data.token;
}
