from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import time
import uuid
from urllib.parse import quote

import httpx

from app.config import settings


def _percent_encode(value: str) -> str:
    # Alibaba's RPC signature keeps "~" unescaped (matches RFC 3986); Python's
    # quote() already treats "~" as safe by default, so this is just explicit.
    return quote(str(value), safe="~")


def _canonicalized_query_string(params: dict[str, str]) -> str:
    return "&".join(f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted(params.items()))


def _sign_alibaba_request(params: dict[str, str], access_key_secret: str) -> str:
    """Alibaba Cloud RPC API signature v1.0 (HMAC-SHA1).

    Docs: https://help.aliyun.com/zh/cmn/developer-reference/signature-mechanism
    """
    canonicalized = _canonicalized_query_string(params)
    string_to_sign = f"GET&%2F&{_percent_encode(canonicalized)}"
    digest = hmac.new(
        f"{access_key_secret}&".encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")


def is_placeholder_key(value: str) -> bool:
    return not value or value.strip().upper().startswith("REPLACE_")


def alibaba_credentials_configured() -> bool:
    return not any(
        is_placeholder_key(value)
        for value in (
            settings.alibaba_access_key_id,
            settings.alibaba_access_key_secret,
            settings.alibaba_app_key,
        )
    )


class AlibabaTokenManager:
    """Fetches and caches the short-lived X-NLS-Token shared by every Alibaba
    Cloud Intelligent Speech Interaction (NLS) API — ASR and TTS both use it.

    Docs: https://help.aliyun.com/zh/isi/getting-started/use-http-or-https-to-obtain-an-access-token
    Each ASR/TTS provider instance keeps its own manager (and thus its own
    cached token) rather than sharing one globally — simpler, and the extra
    CreateToken call this costs when both are set to "alibaba" is cheap and
    infrequent (tokens are cached until ~1 minute before they expire).
    """

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    async def _fetch_token(self) -> str:
        params = {
            "AccessKeyId": settings.alibaba_access_key_id,
            "Action": "CreateToken",
            "Format": "JSON",
            "RegionId": settings.alibaba_region,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureNonce": str(uuid.uuid4()),
            "SignatureVersion": "1.0",
            "Timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "Version": "2019-02-28",
        }
        params["Signature"] = _sign_alibaba_request(params, settings.alibaba_access_key_secret)

        response = await self._client.get(settings.alibaba_token_base_url, params=params, timeout=10.0)
        response.raise_for_status()
        payload = response.json()

        token_info = payload["Token"]
        self._token = str(token_info["Id"])
        self._token_expires_at = float(token_info["ExpireTime"])
        return self._token

    async def get_token(self) -> str:
        # Refresh a minute early to avoid races with an about-to-expire token.
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token
        return await self._fetch_token()
