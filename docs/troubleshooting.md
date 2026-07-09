# Troubleshooting & Pitfalls

项目开发过程中已踩过的坑，供后续排查与避免重复犯错。遇到新问题时请追加到对应章节。

---

## 移动端 · Expo Go

| 现象 | 原因 | 解决 |
|------|------|------|
| `command not found: npm` | 本机未安装 Node.js | 用 nvm 安装 Node 22，重开终端或 `source ~/.nvm/nvm.sh` |
| `Port 8081 is running...` | 已有 Expo 进程占用端口 | `kill $(lsof -ti:8081)` 后重新 `npm start` |
| Expo Go 首页无扫码按钮 | 新版 UI 靠局域网发现或系统相机扫码 | 用 **iPhone 相机** 扫 Mac 终端二维码；或 Settings 手动输入 `exp://<mac-ip>:8081` |
| `Project is incompatible with this version of Expo Go` | 项目 SDK 与 Expo Go 内置 SDK 不一致 | 查看 Expo Go 显示的 **Supported SDK**（如 54），将项目 `expo` 版本降到同一 SDK |
| App Store「最新」Expo Go 仍不兼容 | 商店版往往落后 CLI 创建的 SDK | 以 Expo Go 内显示的 SDK 为准降级项目，或从 https://expo.dev/go 安装匹配版本 |

---

## 移动端 · 网络与后端联调

| 现象 | 原因 | 解决 |
|------|------|------|
| `Network request failed` | 真机使用了 `localhost` / `127.0.0.1` | 必须用 Mac 局域网 IP，如 `http://192.168.1.9:8000`；勿在 `app.config.ts` 写死 localhost |
| `Network request failed` | 后端未启动或未监听 `0.0.0.0` | `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| `Network request failed` | 手机与 Mac 不在同一 Wi-Fi / 路由器 AP 隔离 | 连同一网络；关闭访客网络隔离 |
| `HTTP 405` on Fetch Dev Token | `fetch()` 默认 **GET**，后端接口是 **POST** | 使用 `method: "POST"`，或统一走 `src/services/backendApi.ts` |
| WebSocket 连不上 | WS URL 用了 localhost | 改为 `ws://<mac-ip>:8000/v1/realtime/session` |

### 真机地址规则（必记）

```
❌ http://localhost:8000          → 指向手机自己
✅ http://192.168.x.x:8000        → 指向开发机 Mac
```

Mac 查 IP：`ipconfig getifaddr en0`

---

## 后端

| 现象 | 原因 | 解决 |
|------|------|------|
| 手机访问不到 API | 只监听了 `127.0.0.1` | 启动时加 `--host 0.0.0.0` |
| WebSocket 鉴权失败 | 部分环境不支持自定义 Header | 已支持 query `?token=` 作为备选 |

---

## SDK 版本对照（记录当时环境）

| 日期 | Expo Go Supported SDK | 项目 `expo` 版本 |
|------|----------------------|------------------|
| 2026-07 | 54 | `~54.0.35` |

升级 Expo Go 或项目 SDK 后，请更新此表并跑一遍「Fetch Dev Token → Connect → Send Text」。

---

## 阶段 1 验收清单（Expo Go）

- [ ] `npm start` 正常，终端有 `exp://<ip>:8081`
- [ ] Expo Go 能打开 App，不白屏
- [ ] Backend HTTP URL 为局域网 IP（非 localhost）
- [ ] **Fetch Dev Token** → `token ready`
- [ ] **Connect** → `session ready`
- [ ] **Send Text** → Agent 有回复
- [ ] **🎙 Start Recording → ⏹ Stop & Send** → 有 Transcript / Feedback，Agent 回复自动朗读

---

## LLM / TTS / ASR 接入记录

| 日期 | 变更 | 说明 |
|------|------|------|
| 2026-07 | LLM 切换为 DeepSeek | OpenAI 兼容接口，`base_url=https://api.deepseek.com`，默认模型 `deepseek-v4-flash`；未配置 `DEEPSEEK_API_KEY` 时自动回退为 `[DeepSeek API key not configured] Echo: ...` 占位回复，不会报错中断链路 |
| 2026-07 | 移动端播放 Agent Audio | 用 `expo-av` + `expo-file-system/legacy` 把 PCM16 包成 WAV 文件后播放；检测到 TTS 占位标记（`ELEVENLABS_AUDIO::` / `AZURE_AUDIO::`）会跳过播放并在 UI 显示原因，避免播放无意义噪音 |
| 2026-07 | 移动端真实录音上传 | 新建 `mobile/src/services/audioRecorder.ts`，用 `expo-av` 录制单声道 16kHz `.m4a`（自定义 `RecordingOptions`，同时兼容 Deepgram 与 Alibaba NLS 的采样率限制），停止后读取为 Base64，通过 `audio.chunk`（`format: "m4a"`）+ `audio.commit` 发送给后端；`SessionScreen` 用「🎙 Start Recording / ⏹ Stop & Send」按钮替换了原来的 Mock Voice Turn |
| 2026-07 | 后端接入真实 Deepgram ASR | 修复 `session_agent.py` 中 `audio.commit` 丢弃真实音频的 Bug（改为使用 `audio.chunk` 阶段缓存的 `pending_audio_base64`/`pending_audio_format`）；新增 `DeepgramASRProvider`（`httpx` 调用 Prerecorded API `POST /v1/listen`）；未配置 `DEEPGRAM_API_KEY` 时返回 `[Deepgram API key not configured]` 占位转写，不中断链路；只有 `audio.commit`（`is_final=True`）才会真正调用 Deepgram，避免重复计费 |
| 2026-07 | 移动端本地朗读（TTS） | 新建 `mobile/src/services/textToSpeech.ts`，用 Expo Go 内置的 `expo-speech` 朗读 `agent.text`，完全本地播放、无需任何 API Key；`SessionScreen` 收到 `agent.text` 自动朗读，并新增「🔊 Replay Agent Reply」按钮可重新播放最近一条回复，`Voice: idle/speaking` 状态栏展示朗读状态 |
| 2026-07 | 新增 Alibaba Cloud NLS 作为 ASR 备选 | 新增 `AlibabaASRProvider`（`backend/app/providers/asr_provider.py`），用 `ALIBABA_ACCESS_KEY_ID/SECRET` 按阿里云 RPC 签名算法自动换取并缓存 `X-NLS-Token`（提前 60s 刷新），再调用一句话识别 `POST /stream/v1/asr`；`ASR_PROVIDER=alibaba` 即可切换，`deepgram`/`alibaba` 可随时通过环境变量互换；未配置凭证时返回 `[Alibaba Cloud NLS credentials not configured]` 占位转写。同步把移动端录音格式改为单声道 16kHz（阿里云一句话识别只支持 8000/16000Hz 单声道），Deepgram 端不受影响 |

### 如何真正启用 DeepSeek 回复
1. `cd backend && cp .env.example .env`
2. 编辑 `.env`，把 `DEEPSEEK_API_KEY=REPLACE_WITH_DEEPSEEK_API_KEY` 换成真实 key
3. 重启后端（`uvicorn ... --reload` 会自动重载 `.env` 变化需要重启进程，非 hot reload 生效需重启）
4. Send Text 后应看到自然语言回复，不再有 `[DeepSeek API key not configured]` 前缀

### 何时能听到真实语音
- 目前云端 TTS（`ElevenLabsTTSProvider` / `AzureTTSProvider`）仍是占位实现，只返回文本编码的假字节
- 移动端会检测占位标记并跳过播放，`Agent audio` 状态栏会显示 `placeholder TTS bytes — connect a real TTS provider to hear audio`
- 接入真实云端 TTS（返回真实 PCM16/WAV 字节）后，无需改动前端播放逻辑即可自动生效
- **注意**：这与「本地朗读」是两条独立链路——`expo-speech` 本地朗读已经是真实语音（系统 TTS），无需等待云端 TTS 接入

### 如何真正启用 Deepgram 语音识别
1. 去 [Deepgram 控制台](https://console.deepgram.com/signup) 注册并申请 API Key
2. `backend/.env` 中把 `DEEPGRAM_API_KEY=REPLACE_WITH_DEEPGRAM_API_KEY` 换成真实 key
3. 重启后端进程（同 DeepSeek，`.env` 变化需要重启，非 uvicorn `--reload` 热更新范围）
4. 手机上「🎙 Start Recording → ⏹ Stop & Send」说一句英文，Transcript 应显示真实转写文本，不再是 `[Deepgram API key not configured]`
5. 未配置 Key 时链路仍然可用：转写为占位文本 → 仍会正常触发 LLM 回复与本地朗读，便于先验证录音/播放链路

### 如何切换到 Alibaba Cloud NLS（一句话识别）并申请凭证
1. **申请 AppKey**：打开[智能语音交互控制台](https://nls-portal.console.aliyun.com/)，创建项目（选择"一句话识别"能力），拿到 **AppKey**
2. **申请 AccessKey**：打开[RAM 访问控制控制台](https://ram.console.aliyun.com/manage/ak)，创建一对 **AccessKey ID / AccessKey Secret**（建议用子账号并只授予语音识别相关权限，不要用主账号 AccessKey）
3. 编辑 `backend/.env`：
   - 把 `ALIBABA_ACCESS_KEY_ID` / `ALIBABA_ACCESS_KEY_SECRET` / `ALIBABA_APP_KEY` 换成真实值
   - 把 `ASR_PROVIDER=deepgram` 改成 `ASR_PROVIDER=alibaba`
4. 重启后端进程（`.env` 变化需要重启才生效）
5. 手机上录音测试，Transcript 应显示真实转写；如果看到 `[Alibaba NLS error: ...]`，通常是 AppKey/AccessKey 权限或地域（`ALIBABA_REGION`）不匹配，检查控制台项目所在地域是否与 `.env` 一致
6. **不需要手动获取/刷新 Token**——后端会用 AccessKey 自动签名换取 `X-NLS-Token` 并缓存，到期前 60 秒自动刷新
7. 想切回 Deepgram：把 `ASR_PROVIDER` 改回 `deepgram` 并重启即可，两个 Provider 的移动端录音格式（16kHz 单声道 `.m4a`）是共用的，无需再改客户端

**限制**：Alibaba 一句话识别仅支持单声道、8000/16000 Hz 音频，且单次识别时长上限 60 秒；`mobile/src/services/audioRecorder.ts` 已固定录制 16kHz 单声道，两个 Provider 都兼容。

## 新增条目模板

```markdown
### 简短标题
- **现象**：
- **原因**：
- **解决**：
- **预防**：（可选：代码/规则/文档改动）
```
