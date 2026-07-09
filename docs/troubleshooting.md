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

## 录音对话时同时听到两个声音（云端 TTS + 手机本地朗读）

- **现象**：语音录音对话时,一句回复听到两个声音同时/重叠播放。
- **原因**：`SessionScreen.tsx` 之前对 `agent.text` 和 `agent.audio` 是各自独立处理的——收到 `agent.text` 就立刻用手机本地 `expo-speech` 朗读一次,收到 `agent.audio` 又会再播放一次云端合成的音频。以前云端 TTS 是占位假数据、播放会被跳过,所以只听到本地朗读一个声音；接入 Deepgram Aura-2 真实 TTS 后，两条播放路径都变成真实有声音了，就出现了重叠。
- **解决**：加了一个 `expectAudioReplyRef` 标记区分两种对话路径——语音录音（`audio.commit`）预期后面会有 `agent.audio`，收到 `agent.text` 先不朗读，等 `agent.audio` 到了再播云端音频；只有云端音频是占位/失败时才回退到手机本地朗读兜底。文字对话（`session.input_text`）从来不会有 `agent.audio`，收到 `agent.text` 照常立刻本地朗读，不受影响。
- **预防**：以后如果给 `agent.text`/`agent.audio` 任一路径加新的自动播放逻辑，注意两者是同一次对话的一体两面，不要让两条链路各自无条件地触发播放。

## Agent 语音听起来生硬、不够"标准美音"

- **原因**：早期 `TTS_PROVIDER=elevenlabs`/`azure` 都只是占位代码（`ElevenLabsTTSProvider`/`AzureTTSProvider` 从不真正调用云端 API，只返回带标记的假字节），手机端检测到占位字节会跳过播放，实际听到的声音全部来自**手机本地系统 TTS**（`expo-speech` → iOS `AVSpeechSynthesizer`），音质天然比不上云端神经网络 TTS。
- **已解决**：接入了 **Deepgram Aura-2**（`TTS_PROVIDER=deepgram`），复用已有的 `DEEPGRAM_API_KEY`（和 ASR 同一个账号，不需要新申请 key）。现在 `agent.audio` 里是真实合成的 PCM16 音频，本机 `expo-speech` 只在这条链路失败/未配置时才会作为兜底。
- 想换音色：改 `DEEPGRAM_TTS_MODEL`（默认 `aura-2-thalia-en`），完整列表见 https://developers.deepgram.com/docs/tts-models 。改完记得重启后端（本机 `.env` 和服务器 `.env` 是两份独立配置，别只改一边）。
- 如果 `agent.audio` 又开始不出声，检查 Transcript/日志里是否又出现 `DEEPGRAM_TTS_PLACEHOLDER::`（key 未配置）或 `DEEPGRAM_TTS_ERROR::`（请求失败，通常是 key 或配额问题）字样,原理和 ASR 那节的排查方法一样。

## Agent 回复很怪（比如一直提"audio tool having a hiccup"）

- **现象**：点击 Start Recording 说话后，Agent 文字回复完全不像在回应你说的内容，反而像是在聊"设备/工具有点问题"这种奇怪话题；Transcript 框里显示的也不是你说的话。
- **原因**：ASR（Deepgram/Alibaba）没配置真实 Key 或请求失败时，会返回一段**人类可读的占位/报错文案**（例如 `[Deepgram API key not configured — set DEEPGRAM_API_KEY]`），这段文案会被当作"学员说的话"直接传给 LLM。LLM 不知道这是系统错误，只会当成普通对话内容去自然回应，于是就聊出一些看起来语无伦次、实际是在回应报错信息的话。
- **排查方法**：先看 App 里的 **Transcript** 框（不是 Agent 回复框）——如果显示的是方括号包起来的英文提示（`[Deepgram ...]` / `[Alibaba ...]`）而不是你说的话，说明问题在 ASR 这一层，和 LLM/网络无关。
- **解决**：确认对应后端（本机或服务器）的 `.env` 里 `DEEPGRAM_API_KEY`（或 `ALIBABA_ACCESS_KEY_*`）是真实值而不是 `REPLACE_WITH_...` 占位符，改完记得重启后端进程（`uvicorn --reload` 不会重新读 `.env`，systemd 也要手动 `systemctl restart`）。
- **预防**：本机和服务器是两份独立的 `.env`，配置一个 Key 时容易忘记同步另一份——每次新增/换 Key 后，最好都用 `grep -q '^KEY_NAME=' .env` 分别在本机和服务器上确认一下（不要 `cat`/打印真实值），别只改了一边。

## 装到 iPhone 是否必须和 Mac 同一局域网

**现状**：Expo Go 模式下"扫码打开"本质是让手机上早就装好的 Expo Go 去 Mac 的 Metro 开发服务器拉 JS 代码，默认走局域网发现，所以必须同一 Wi-Fi。

**三种解法：**

| 方案 | 要不要同局域网 | 要不要一直开着 Mac | 成本 |
|------|------|------|------|
| `npm start`（默认 `--lan`） | 需要 | 需要 | 免费 |
| `npm run start:tunnel` | **不需要**（走 ngrok 隧道，任意网络能连） | 仍需要 | 免费 |
| EAS Build + TestFlight 打真包 | 不需要 | **不需要**，装完是独立 App | 需要 Apple Developer Program（$99/年） |

已经把 `npm run start:tunnel` 加进了 `mobile/package.json`（依赖 `@expo/ngrok`，已装好）。用法和 `npm start` 一样，扫码或手动在 Expo Go 里粘贴 `exp://` 链接即可，不挑网络，只是延迟比局域网略高（流量经过 ngrok 中转）。

如果想要真正"装一次以后完全脱离 Mac/网络限制"的体验，需要走 EAS Build + TestFlight，那条路需要先注册 Apple Developer Program（$99/年）。

## 后端改动的工作流规范（代码 vs .env）

- **代码改动（`.py`、`requirements*.txt` 等受 git 管理的文件）**：本地改 → `cd backend && pytest` 跑通 → `git commit` + `git push` → 服务器上 `git pull` 拉取。**不要**再直接 SSH 上服务器改代码或 `scp` 文件上去——那样会导致服务器 git 仓库出现"未提交的本地改动"，下次 `git pull` 会被挡住，需要手动 `git checkout -- <file>` 才能继续（踩过这个坑，见本次改动记录）。
- **`.env` 文件**：本机和服务器各自独立维护，永远不会、也不应该通过 git 同步——两边的 Provider 选择本来就可能不同（比如本机 `ASR_PROVIDER=alibaba`、服务器 `ASR_PROVIDER=deepgram`），这是正常现象不是 bug。每次改完服务器的 `.env` 记得 `sudo systemctl restart ai-english-backend`（`--reload` 只监听代码文件，不会重新读 `.env`）。
- 完整规范和示例命令见 `.cursor/rules/backend-deployment-workflow.mdc`。

## 服务器部署（腾讯云）

后端已部署在腾讯云服务器（`152.136.254.150`），排查结论记录如下：

### 移动端能直接访问远程后端吗
- **可以**：`http://152.136.254.150:8000` 已从公网验证可达（`curl` 直接测通 `/docs`、`/healthz`）。
- 只需在 App 里把 **Backend HTTP URL** / **Backend WebSocket URL** 改成：
  - `http://152.136.254.150:8000`
  - `ws://152.136.254.150:8000/v1/realtime/session`
  - 或直接用 `mobile/.env`（见 `mobile/.env.example`）设置默认值，无需每次手填。
- Expo Go 对明文 HTTP 比较宽松，调试阶段够用；**但没有 TLS**，正式打包/上架前必须换成域名 + HTTPS（`wss://`），否则会被 iOS ATS / Android 明文流量策略拦掉。
- 80/443 端口当前对公网不可达（安全组大概率只放了 22 和 8000），Caddy 目前也只是返回默认静态页，没有反代到后端——如果要上 HTTPS，需要：申请域名 → 安全组放开 80/443 → 配置 Caddy 反代到 `127.0.0.1:8000` 并让它自动签发证书。

### 后端常驻性
- 之前是手动跑的 `uvicorn`，SSH 断开或服务器重启就会挂掉。
- 已改为 systemd 托管：`/etc/systemd/system/ai-english-backend.service`（`systemctl enable --now` 已执行），崩溃自动重启、开机自启。
- 常用命令：`sudo systemctl status/restart/stop ai-english-backend`，日志 `sudo journalctl -u ai-english-backend -f`。
- **改了 `backend/.env` 后必须 `sudo systemctl restart ai-english-backend`**（`--reload` 只监听代码文件变化，不会重新读 `.env`）。

### LLM 配置差异
- 服务器 `.env` 里 `LLM_PROVIDER` 曾是 `openai`，但 `OpenAILLMProvider` 只是占位模板（不真正调用任何 API），和本地验证过的 DeepSeek 效果不一样。
- 已切换为 `LLM_PROVIDER=deepseek` 并同步了 `DEEPSEEK_API_KEY`，重启后端后用真实 WebSocket 会话验证过：`providerRoute.llm == "deepseek"`，回复是真实生成的句子而不是模板。

## Swagger UI 能否用于自动化接口测试

结论：**Swagger UI 本身是给人看的交互页面**，不是能直接"塞进"自动化流程的东西；但它背后的 OpenAPI schema（`GET /openapi.json`，FastAPI 自动生成）正是自动化工具需要的输入。已落地方案：

- `backend/tests/`：pytest + FastAPI `TestClient`，覆盖 `/healthz`、`/v1/auth/dev-token`、完整的 `/v1/realtime/session` WebSocket 流程（鉴权失败、`session.start/audio.chunk/audio.commit/session.input_text/session.stop`、未知事件类型），以及 `evaluation`/`lesson_planner` 纯函数。运行：`cd backend && pip install -r requirements-dev.txt && pytest`。
- `tests/conftest.py` 在导入 app 之前把所有 provider 的 API Key 强制设为占位值，保证测试离线运行、不消耗真实配额、不受本机 `.env` 内容影响，适合接入 CI。
- 如果还想要契约/模糊测试，可以在此基础上加 [schemathesis](https://schemathesis.readthedocs.io/)，直接指向线上 `openapi.json` 跑：`schemathesis run http://152.136.254.150:8000/openapi.json`——不需要额外写用例，能自动发现 schema 与实际响应不一致的问题。

## 新增条目模板

```markdown
### 简短标题
- **现象**：
- **原因**：
- **解决**：
- **预防**：（可选：代码/规则/文档改动）
```
