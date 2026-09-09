# Web + Desktop update (2026-09-09)

## Start

Build with `cd web && npm run build`, then from project root `bash scripts/run_web.sh`.
Open http://127.0.0.1:8001/ ; Desktop Operator URL uses the same port.
Scripts bind loopback, not LAN. macOS launcher defaults to Ollama; override LLM_BACKEND/RAG_BACKEND for other installed runtimes.
Do not start a second server on the same port. Restart the existing server after backend changes.
The frontend root is project/web/dist; its original parents[2] calculation was correct.
The outage was an unavailable/stale server/build and port inconsistency, not that path calculation.

## KKU fallback

Web: configure KKU_API_KEY in the server environment (or local .env, never commit it).
KKU_VISION_MODELS and KKU_CHAT_MODELS are comma-separated fallback orders.
Then enable the separate remembered consent checkboxes for OCR/chat in Web Chat.
Desktop: use Settings > KKU / Router; key remains encrypted on disk. For OCR only,
the main process passes the key in a request header to the selected loopback Airis runtime.
Do not point this runtime URL at an untrusted process. The key is never returned to the browser.

OCR: local vision → native OCR → optional KKU when no text/error/repeated illegible markers.
Images are now read as documents in Web Chat, not automatically sent to image classification.
Scanned PDF pages are rendered to images; raw PDF bytes are not falsely sent as an image.
On quota/model-unavailable responses try configured models in order. Selected models must actually support vision.
Desktop native PDF/text extraction remains first. Images use OCR unless Vision is enabled for direct image chat.
OCR currently needs the Airis runtime. If that runtime is down, Desktop reports an error rather than claiming extraction succeeded.
Unsupported executables/archives or corrupt documents are not made readable merely by using an API key.

Web chat: only fallback on Local error/timeout/configured fallback response; send conversation, question and attached text with explicit consent.
Does not retry an OS action or an Extension write through an LLM. Does not grant OAuth permissions.
Web does not yet have Desktop's complexity router or independent verifier; KKU answers are labelled not cross-verified.
Native local inference may continue after disconnect until its worker finishes; no claim of undo or immediate native cancellation.
No live KKU calls were made in this update. Availability/quota/cost must be checked against the user's account.

## Extensions

Open /#extensions or use Desktop's Extensions button.
Existing registry supports Gmail, Drive, Calendar, GitHub, Notion and Slack; no claim to support all possible third-party plugins.
All six were listed live, all currently disconnected. Provider Client ID/Secret and OAuth grants are still required.
Callback default now uses http://127.0.0.1:8001 — existing registered callbacks may need updating.
Refresh status after returning from OAuth. High-risk write confirmations remain.
Custom MCP servers and additional services are still pending, not implicitly enabled.

## Tests / remaining work

27 targeted Python tests and 17 Desktop backend tests passed; Desktop Electron regression passed.
Browser verified Chat, consent controls, Extensions list and HTTP 200.
Cloud fallback uses mocks; no key, microphone/camera permission or external account was used.
Operator consent is remembered separately per Web origin and Desktop runtime; both have a forget control.
Remaining: live KKU/vision tests, OAuth accounts, MCP, code sandbox, hardware/location,
full Web/Desktop parity, model capability discovery, and Windows installer verification.
