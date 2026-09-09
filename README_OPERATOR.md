# Operator

Open Airis and choose **Operator**. Select session permissions and start; microphone and camera remain off until their buttons are pressed. End session revokes the server token, stops media tracks, closes tracking/audio resources and stops speech. Refreshing starts without permissions.

## Local runtime

- Main model defaults to qwen3.6:35b-a3b-q4_K_M via local Ollama.
- RAG automatically selects an installed coding/general model based on query and context length, falling back to the main model when unavailable. No RAG selector is shown.
- Speech input: local faster-whisper base on CPU, VAD-delimited utterances (up to 12 seconds). Browser speech recognition services are not used. Noise and accents can affect transcripts; use the visible transcript or typed commands when needed.
- Speech output: browser voices marked localService only. If none is available the UI reports text-only output.
- Speaking can be interrupted by detected microphone audio; echo cancellation is requested. Headphones improve interruption detection.
- Camera/hand inference uses local MediaPipe WASM and the bundled gesture model, not a cloud API. Palm hold activates listening only with voice permission, pinch selects marked buttons/drags the panel, swipe selects a panel, fist stops waiting/speech. Cancellation does not undo a completed action.
- Coding/Research/Task/Memory are UI panels and tool destinations, not autonomous agents.

## Commands

- switch to camera / show my view / เปิดกล้อง
- switch to core / ปิดกล้อง
- start listening / เริ่มฟัง
- cancel / ยกเลิก / หยุด
- search files budget / ค้นหาไฟล์ budget: filename search only, scoped to the explicitly permitted folder, up to 15,000 entries and 12 results. Hidden folders, dependency folders and symlinks are skipped. No file content or calendar provider access is implied.
- query memory keyword / ค้นความจำ keyword: searches the Airis memory store with permission.
- open app Calculator / เปิดแอป Notes: macOS allowlist: Calculator, Notes, Safari, TextEdit.
- run workflow focus: opens Notes and Calculator, requiring system permission.
- start task title / เริ่มงาน title: adds to an in-session task list; does not launch a background agent or shell.

Deletes, sends, purchases and arbitrary shell commands are not exposed by Operator. The UI explains this rather than treating an LLM response as successful execution. Existing Extensions retain their confirmation flow; Operator does not invoke them.

## Setup on another machine

Install requirements-operator.txt, run npm ci in web/, and copy @mediapipe/tasks-vision/wasm files to web/public/operator/wasm. The gesture model is bundled under web/public/operator.
Cache the speech model once with:

    .venv/bin/python -c 'from faster_whisper import WhisperModel; WhisperModel("base", device="cpu", compute_type="int8")'

Runtime transcription uses local_files_only=True and never downloads a model. Initial asset/model downloads require internet; subsequent inference has no subscription/API fee. Hardware, power and internet service remain user costs.

Local transcription, permission rejection/revocation, scoped search, RAG routing, UI task creation and frontend build were tested. Physical microphone/camera/hand-gesture testing requires the user's session permission and has not been performed by the agent.

References: https://github.com/SYSTRAN/faster-whisper and https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/web_js
