import React, { useEffect, useRef, useState } from "react";
import { FilesetResolver, GestureRecognizer } from "@mediapipe/tasks-vision";
import "./operator.css";
import { dragUpdate, LatestVoiceQueue } from "../operatorRuntime";
import OperatorCore from "../components/OperatorCore";
import { selectModel } from "../api/client";

const panels = ["Coding", "Research", "Task", "Memory"];
type Entry = { text: string; source?: string; at: string };

function tokenLabel(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "ไม่ระบุโดย KKU";
  return new Intl.NumberFormat("en-US").format(value);
}

function observedLabel(value: any) {
  if (!value || typeof value !== "object") return "ยังไม่มีข้อมูลจากการใช้งานจริง";
  const usage = value.usage || {};
  const quota = value.model_quota || {};
  const quotaParts = [
    quota.daily_quota_tokens !== undefined ? `โควตารายวัน ${tokenLabel(quota.daily_quota_tokens)}` : "",
    quota.daily_usage_tokens !== undefined ? `ใช้ไป ${tokenLabel(quota.daily_usage_tokens)}` : "",
    quota.daily_remaining_tokens !== undefined ? `เหลือ ${tokenLabel(quota.daily_remaining_tokens)}` : "",
  ].filter(Boolean);
  if (quotaParts.length) return quotaParts.join(" · ");
  const total = usage.total_tokens;
  if (typeof total === "number") return `ใช้ล่าสุด ${tokenLabel(total)} tokens`;
  return "พบข้อมูลจากการเรียกใช้จริง";
}

function QuotaDetails({ observed }: { observed: any }) {
  const quota = observed?.model_quota;
  const usage = observed?.usage;
  const limit = quota?.daily_quota_tokens;
  const remaining = quota?.daily_remaining_tokens;
  const used = quota?.daily_usage_tokens;
  const progress = typeof limit === "number" && limit > 0 && typeof used === "number"
    ? Math.max(0, Math.min(100, used / limit * 100)) : null;
  return (
    <div className="op-quota">
      <div className="op-quota-heading">
        <span>โควตารายวัน · tokens</span>
        <strong className={remaining === 0 ? "exhausted" : ""}>
          {typeof remaining === "number" ? `เหลือ ${tokenLabel(remaining)}` : "ยังไม่รายงาน"}
        </strong>
      </div>
      {progress !== null && (
        <progress value={progress} max={100} aria-label="สัดส่วนโควตา KKU ที่ใช้แล้ว" />
      )}
      <small>{quota ? observedLabel(observed) : "รอข้อมูลโควตาจากคำตอบ KKU ครั้งถัดไป"}</small>
      {usage && <small>คำขอล่าสุด: เข้า {tokenLabel(usage.prompt_tokens ?? usage.input_tokens)} · ออก {tokenLabel(usage.completion_tokens ?? usage.output_tokens)} · รวม {tokenLabel(usage.total_tokens)}</small>}
      {observed?.last_seen && <small>ข้อมูล ณ {new Date(observed.last_seen * 1000).toLocaleString("th-TH")} · อาจเปลี่ยนเมื่อใช้จากแอปอื่น</small>}
    </div>
  );
}

function capabilityLabel(key: string) {
  const labels: Record<string, string> = {
    chat: "แชต",
    vision: "อ่านภาพ",
    web_search: "ค้นเว็บผ่าน Airis",
    website_generation: "สร้างเว็บ / HTML",
    image_generation: "สร้างภาพโดยตรง",
  };
  return labels[key] || key;
}

export default function Operator() {
  const [grants, setGrants] = useState<string[]>([]),
    [root, setRoot] = useState(""),
    [token, setToken] = useState(""),
    [state, setState] = useState("Idle"),
    [view, setView] = useState("core"),
    [panel, setPanel] = useState("Research"),
    [text, setText] = useState(""),
    [entries, setEntries] = useState<Entry[]>([]),
    [results, setResults] = useState<any[]>([]),
    [gesture, setGesture] = useState(""),
    [level, setLevel] = useState(0),
    [offset, setOffset] = useState({ x: 0, y: 0 }),
    [facing, setFacing] = useState("user");
  const video = useRef<HTMLVideoElement>(null),
    canvas = useRef<HTMLCanvasElement>(null),
    mic = useRef<MediaStream | null>(null),
    camera = useRef<MediaStream | null>(null),
    audio = useRef<AudioContext | null>(null),
    recorder = useRef<MediaRecorder | null>(null),
    recognizer = useRef<GestureRecognizer | null>(null),
    request = useRef<AbortController | null>(null),
    life = useRef(0),
    frames = useRef<number[]>([]),
    session = useRef(""),
    voiceOn = useRef(false),
    panelRef = useRef(panel),
    actions = useRef<any>({});
  const permissionDialog = useRef<HTMLDialogElement>(null),
    startingRef = useRef(false);
  const [starting, setStarting] = useState(false),
    [sessionError, setSessionError] = useState("");
  const [remembered, setRemembered] = useState(false);
  useEffect(() => {
    try {
      const value = JSON.parse(
        localStorage.getItem("airis.operator.consent") || "null",
      );
      const allowed = [
        "voice",
        "camera",
        "files",
        "web",
        "memory",
        "system",
        "location",
        "environment",
        "telemetry",
        "pointer",
      ];
      if (
        value?.version === 1 &&
        Array.isArray(value.permissions) &&
        value.permissions.every((p: string) => allowed.includes(p)) &&
        typeof value.root === "string"
      ) {
        setGrants(value.permissions);
        setRoot(value.root);
        setRemembered(true);
      }
    } catch {}
  }, []);
  const begin = () => {
    if (remembered) void start();
    else setPermissionOpen(true);
  };
  const forget = () => {
    stop();
    localStorage.removeItem("airis.operator.consent");
    setRemembered(false);
    setGrants([]);
    setRoot("");
    setPermissionOpen(true);
  };
  const voiceQueue = useRef<LatestVoiceQueue<Blob> | null>(null),
    transcription = useRef<AbortController | null>(null),
    micEpoch = useRef(0),
    micOpening = useRef(false);
  const [permissionOpen, setPermissionOpen] = useState(false),
    [now, setNow] = useState(new Date()),
    [modelInfo, setModelInfo] = useState<any>(null),
    [imageInfo, setImageInfo] = useState<any>(null),
    [systemInfo, setSystemInfo] = useState<any>(null),
    [online, setOnline] = useState(false),
    [modelQuery, setModelQuery] = useState(""),
    [switchingModel, setSwitchingModel] = useState(""),
    [modelNotice, setModelNotice] = useState(""),
    [modelStatusError, setModelStatusError] = useState(""),
    [refreshingModels, setRefreshingModels] = useState(false);
  const refreshModels = useRef<() => Promise<void>>(async () => {});
  useEffect(() => {
    const controller = new AbortController();
    const clock = setInterval(() => setNow(new Date()), 1000);
    let refreshing = false;
    const refresh = async () => {
      if (refreshing || controller.signal.aborted) return;
      refreshing = true;
      setRefreshingModels(true);
      try {
        const [m, s, img] = await Promise.allSettled(
          ["/api/models", "/api/dashboard/system", "/api/images/status"].map((url) =>
            fetch(url, { signal: controller.signal }).then((r) => {
              if (!r.ok) throw Error("Status unavailable");
              return r.json();
            }),
          ),
        );
        if (!controller.signal.aborted) {
          if (m.status === "fulfilled") setModelInfo(m.value);
          if (s.status === "fulfilled") setSystemInfo(s.value);
          setImageInfo(img.status === "fulfilled" ? img.value : null);
          setOnline(m.status === "fulfilled" && s.status === "fulfilled");
          setModelStatusError(m.status === "fulfilled" ? "" : "อัปเดตข้อมูลโมเดลไม่ได้ · กำลังแสดงข้อมูลล่าสุดที่โหลดสำเร็จ");
        }
      } catch {
        if (!controller.signal.aborted) setOnline(false);
      } finally {
        refreshing = false;
        if (!controller.signal.aborted) setRefreshingModels(false);
      }
    };
    refreshModels.current = refresh;
    void refresh();
    const timer = setInterval(refresh, 15000);
    return () => {
      controller.abort();
      clearInterval(clock);
      clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    if (permissionOpen && !token) permissionDialog.current?.showModal();
  }, [permissionOpen, token]);
  panelRef.current = panel;
  const log = (message: string, source = "UI") =>
    setEntries((v) => [
      ...v.slice(-29),
      { text: message, source, at: new Date().toLocaleTimeString() },
    ]);
  const headers = () => ({ "X-Operator-Session": session.current });
  const cue = (kind: "ready" | "listen" | "done") => {
    try {
      const Ctx = window.AudioContext || (window as any).webkitAudioContext;
      if (!Ctx) return;
      const ctx = new Ctx(),
        gain = ctx.createGain(),
        now = ctx.currentTime;
      gain.connect(ctx.destination);
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.055, now + 0.012);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.22);
      const notes =
        kind === "listen"
          ? [520, 780]
          : kind === "done"
            ? [740, 540]
            : [420, 630];
      notes.forEach((frequency, index) => {
        const osc = ctx.createOscillator();
        osc.type = "sine";
        osc.frequency.setValueAtTime(frequency, now + index * 0.07);
        osc.connect(gain);
        osc.start(now + index * 0.07);
        osc.stop(now + 0.24);
      });
      setTimeout(() => void ctx.close(), 350);
    } catch {}
  };
  const speak = (message: string) => {
    if (!grants.includes("voice")) {
      setState("Idle");
      return;
    }
    speechSynthesis.cancel();
    const thai = /[ก-๙]/.test(message);
    const local = speechSynthesis.getVoices().filter((v) => v.localService);
    const matching = local.filter((v) =>
      v.lang.toLowerCase().startsWith(thai ? "th" : "en"),
    );
    const preferred = thai
      ? ["kanya", "narisa", "premwadee"]
      : ["daniel", "oliver", "arthur", "jamie", "serena"];
    const voice =
      preferred
        .map((name) =>
          matching.find((v) => v.name.toLowerCase().includes(name)),
        )
        .find(Boolean) ||
      matching[0] ||
      local[0];
    if (!voice) {
      setState(voiceOn.current ? "Listening" : "Idle");
      log("No local voice is available. Showing the response as text.", "voice");
      return;
    }
    const spoken = message
      .replace(/https?:\/\/\S+/g, "reference link")
      .replace(/[*_`#>|]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
    const utterance = new SpeechSynthesisUtterance(spoken);
    utterance.voice = voice;
    utterance.lang = voice.lang;
    utterance.rate = thai ? 0.96 : 0.92;
    utterance.pitch = thai ? 0.9 : 0.78;
    utterance.volume = 1;
    utterance.onstart = () => setState("Speaking");
    utterance.onend = () => {
      cue("done");
      setState(voiceOn.current ? "Listening" : "Idle");
    };
    utterance.onerror = () => setState(voiceOn.current ? "Listening" : "Idle");
    setState("Speaking");
    speechSynthesis.speak(utterance);
  };
  const cancel = () => {
    voiceQueue.current?.invalidate();
    if (session.current)
      fetch("/api/operator/pending", {
        method: "DELETE",
        headers: headers(),
      }).catch(() => {});
    life.current++;
    request.current?.abort();
    speechSynthesis.cancel();
    setState(voiceOn.current ? "Listening" : "Idle");
    log(
      "Stopped the pending response and speech. Completed actions cannot be undone.",
      "cancel",
    );
  };
  const stopMic = () => {
    micEpoch.current++;
    micOpening.current = false;
    voiceQueue.current?.close();
    transcription.current?.abort();
    voiceOn.current = false;
    recorder.current?.state === "recording" && recorder.current.stop();
    mic.current?.getTracks().forEach((t) => t.stop());
    mic.current = null;
    audio.current?.close();
    audio.current = null;
    setLevel(0);
    setState("Idle");
  };
  const stopCamera = () => {
    camera.current?.getTracks().forEach((t) => t.stop());
    camera.current = null;
    recognizer.current?.close();
    recognizer.current = null;
    setView("core");
    setGesture("");
  };
  const stop = () => {
    life.current++;
    request.current?.abort();
    speechSynthesis.cancel();
    stopMic();
    stopCamera();
    frames.current.forEach(cancelAnimationFrame);
    if (session.current)
      fetch("/api/operator/session", {
        method: "DELETE",
        headers: headers(),
      }).catch(() => {});
    session.current = "";
    setToken("");
  };
  useEffect(
    () => () => {
      stop();
    },
    [],
  );
  const start = async () => {
    if (startingRef.current) return;
    startingRef.current = true;
    setStarting(true);
    setSessionError("");
    const run = life.current;
    try {
      localStorage.setItem(
        "airis.operator.consent",
        JSON.stringify({ version: 1, permissions: grants, root }),
      );
      setRemembered(true);
      const r = await fetch("/api/operator/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ permissions: grants, root }),
      });
      const data = await r.json();
      if (!r.ok) throw Error(data.detail);
      if (run !== life.current) {
        void fetch("/api/operator/session", {
          method: "DELETE",
          headers: { "X-Operator-Session": data.token },
        });
        return;
      }
      session.current = data.token;
      setToken(data.token);
      setPermissionOpen(false);
      setEntries([]);
      setResults([]);
      cue("ready");
      log("Operator session started. Devices are limited to selected permissions.");
    } catch (e: any) {
      setSessionError(e.message);
      log(e.message, "error");
    } finally {
      startingRef.current = false;
      setStarting(false);
    }
  };
  const command = async (value: string) => {
    if (!session.current) return;
    voiceQueue.current?.invalidate();
    const low = value.toLowerCase().trim();
    log(value, "you");
    if (
      ["switch to camera", "show my view", "เปิดกล้อง", "โหมดกล้อง"].some((x) =>
        low.includes(x),
      )
    ) {
      await actions.current.camera();
      return;
    }
    if (["switch to core", "ปิดกล้อง"].some((x) => low.includes(x))) {
      stopCamera();
      log("Switched to AI Core", "switch_view");
      return;
    }
    if (["cancel", "ยกเลิก", "หยุด"].includes(low)) {
      cancel();
      return;
    }
    if (low === "start listening" || low === "เริ่มฟัง") {
      await actions.current.listen();
      return;
    }
    const selected = panels.find(
      (p) => low === p.toLowerCase() || low === "switch to " + p.toLowerCase(),
    );
    if (selected) {
      setPanel(selected);
      log("Active panel: " + selected, "switch_panel");
      return;
    }
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    const run = ++life.current;
    setState("Thinking");
    log(
      low.startsWith("ค้น") ||
        low.startsWith("search") ||
        low.startsWith("query")
        ? "Searching authorized local data…"
        : low.startsWith("เปิดแอป") || low.startsWith("open app")
          ? "Calling open_app…"
          : "Processing locally…",
      "Operator",
    );
    try {
      const r = await fetch("/api/operator/command", {
        method: "POST",
        headers: { ...headers(), "Content-Type": "application/json" },
        body: JSON.stringify({ text: value }),
        signal: controller.signal,
      });
      const data = await r.json();
      if (!r.ok) throw Error(data.detail);
      if (run !== life.current) return;
      setPanel(data.panel || "Research");
      setResults(data.results || []);
      log(data.answer, data.source);
      speak(data.answer);
    } catch (e: any) {
      if (run !== life.current || e.name === "AbortError") return;
      setState(voiceOn.current ? "Listening" : "Idle");
      log(e.message, "error");
    }
  };
  const listen = async () => {
    if (!grants.includes("voice")) {
      log("Microphone permission is required for this session.", "permission");
      return;
    }
    if (voiceOn.current || micOpening.current) return;
    micOpening.current = true;
    const generation = life.current,
      epoch = micEpoch.current;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true },
        video: false,
      });
      if (
        !session.current ||
        generation !== life.current ||
        epoch !== micEpoch.current
      ) {
        stream.getTracks().forEach((t) => t.stop());
        micOpening.current = false;
        return;
      }
      mic.current = stream;
      voiceOn.current = true;
      const ctx = new AudioContext();
      audio.current = ctx;
      await ctx.resume();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      ctx.createMediaStreamSource(stream).connect(analyser);
      const buffer = new Float32Array(analyser.fftSize);
      const queue = new LatestVoiceQueue<Blob>(
        async (blob) => {
          const controller = new AbortController();
          transcription.current = controller;
          const timer = setTimeout(() => controller.abort(), 60000);
          try {
            const form = new FormData();
            form.append("file", blob, "voice.webm");
            const res = await fetch("/api/operator/transcribe", {
              method: "POST",
              headers: headers(),
              body: form,
              signal: controller.signal,
            });
            const data = await res.json();
            if (!res.ok) throw Error(data.detail);
            return data.text || "";
          } finally {
            clearTimeout(timer);
          }
        },
        (value) => {
          if (value) void actions.current.command(value);
          else setState("Listening");
        },
        (e) => {
          log(e instanceof Error ? e.message : String(e), "voice error");
          setState("Listening");
        },
      );
      voiceQueue.current = queue;
      micOpening.current = false;
      let lastVoice = 0,
        startTime = 0;
      const record = () => {
        const revision = queue.invalidate();
        // Barge-in invalidates both model output and old transcription immediately.
        life.current++;
        request.current?.abort();
        speechSynthesis.cancel();
        setState("Listening");
        const r = new MediaRecorder(stream);
        recorder.current = r;
        const chunks: Blob[] = [];
        startTime = performance.now();
        r.ondataavailable = (e) => {
          if (e.data.size) chunks.push(e.data);
        };
        r.onstop = () => {
          if (
            !voiceOn.current ||
            !session.current ||
            epoch !== micEpoch.current
          )
            return;
          const blob = new Blob(chunks, { type: r.mimeType });
          if (blob.size < 1000) return;
          setState("Transcribing");
          queue.submit(blob, revision);
        };
        r.start();
      };
      cue("listen");
      setState("Listening");
      log("Listening — audio is transcribed locally with Whisper.", "voice");
      let ticks = 0;
      const sample = () => {
        if (!voiceOn.current || epoch !== micEpoch.current) return;
        analyser.getFloatTimeDomainData(buffer);
        const rms = Math.sqrt(
          buffer.reduce((sum, x) => sum + x * x, 0) / buffer.length,
        );
        const now = performance.now();
        if (++ticks % 4 === 0) setLevel(Math.min(1, rms * 12));
        if (rms > 0.035) {
          lastVoice = now;
          if (speechSynthesis.speaking) {
            speechSynthesis.cancel();
            setState("Listening");
          }
          if (recorder.current?.state !== "recording") record();
        }
        if (
          recorder.current?.state === "recording" &&
          (now - lastVoice > 800 || now - startTime > 12000)
        )
          recorder.current.stop();
        frames.current[0] = requestAnimationFrame(sample);
      };
      sample();
    } catch (e: any) {
      stopMic();
      log(e.message, "microphone error");
    }
  };
  const switchCamera = async () => {
    if (!grants.includes("camera")) {
      log("Camera permission is required for this session.", "permission");
      return;
    }
    if (camera.current) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: facing, width: 640, height: 480 },
        audio: false,
      });
      if (!session.current) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      camera.current = stream;
      setView("camera");
      if (video.current) {
        video.current.srcObject = stream;
        await video.current.play();
      }
      log("Camera view — local gesture tracking is active", "switch_view");
      const files = await FilesetResolver.forVisionTasks("/operator/wasm");
      const tracker = await GestureRecognizer.createFromOptions(files, {
        baseOptions: { modelAssetPath: "/operator/gesture_recognizer.task" },
        runningMode: "VIDEO",
        numHands: 1,
      });
      if (!camera.current) {
        tracker.close();
        return;
      }
      recognizer.current = tracker;
      let last = 0,
        palm = 0,
        cooldown = 0,
        previousX: number | null = null,
        previousTime = 0,
        pinched = false,
        drag: { x: number; y: number } | null = null;
      const track = () => {
        const v = video.current,
          c = canvas.current;
        if (!camera.current || !recognizer.current || !v || !c) return;
        const now = performance.now();
        if (v.readyState >= 2 && now - last > 90) {
          last = now;
          const detected = tracker.recognizeForVideo(v, now);
          const points = detected.landmarks[0],
            name = detected.gestures[0]?.[0]?.categoryName;
          const context = c.getContext("2d")!;
          c.width = v.videoWidth;
          c.height = v.videoHeight;
          context.clearRect(0, 0, c.width, c.height);
          if (points) {
            context.fillStyle = "#83ffe7";
            points.forEach((p) => {
              context.beginPath();
              context.arc(
                (1 - p.x) * c.width,
                p.y * c.height,
                4,
                0,
                Math.PI * 2,
              );
              context.fill();
            });
            const pinch =
              Math.hypot(points[4].x - points[8].x, points[4].y - points[8].y) <
              0.045;
            if (name === "Open_Palm") {
              if (!palm) palm = now;
              if (now - palm > 1000 && now > cooldown) {
                setGesture("Open palm → Listening");
                actions.current.listen();
                cooldown = now + 1800;
                palm = 0;
              }
            } else palm = 0;
            if (name === "Closed_Fist" && now > cooldown) {
              setGesture("Fist → Cancel");
              actions.current.cancel();
              cooldown = now + 1800;
            }
            const bounds = v.getBoundingClientRect(),
              scale = Math.max(
                bounds.width / v.videoWidth,
                bounds.height / v.videoHeight,
              );
            const x =
                bounds.left +
                (1 - points[8].x) * v.videoWidth * scale -
                (v.videoWidth * scale - bounds.width) / 2,
              y =
                bounds.top +
                points[8].y * v.videoHeight * scale -
                (v.videoHeight * scale - bounds.height) / 2;
            if (pinch && !pinched) {
              const target = document
                .elementFromPoint(x, y)
                ?.closest("[data-gesture]") as HTMLElement | null;
              if (target?.tagName === "BUTTON") target.click();
              else if (target?.classList.contains("operator-panel"))
                drag = { x, y };
              setGesture("Pinch → Select / drag panel");
            }
            if (pinch && drag) {
              setOffset(dragUpdate(drag, { x, y }));
              drag = { x, y };
            }
            if (!pinch) drag = null;
            pinched = pinch;
            if (
              !pinch &&
              previousX !== null &&
              now - previousTime < 300 &&
              Math.abs(points[0].x - previousX) > 0.2 &&
              now > cooldown
            ) {
              const direction = points[0].x > previousX ? -1 : 1;
              setPanel(
                panels[(panels.indexOf(panelRef.current) + direction + 4) % 4],
              );
              setGesture("Swipe → Switch panel");
              cooldown = now + 1000;
            }
            if (now - previousTime > 200) {
              previousX = points[0].x;
              previousTime = now;
            }
          } else {
            palm = 0;
            previousX = null;
            pinched = false;
            drag = null;
          }
        }
        frames.current[1] = requestAnimationFrame(track);
      };
      track();
    } catch (e: any) {
      log(e.message, "camera / gesture error");
      stopCamera();
    }
  };
  actions.current = { command, listen, camera: switchCamera, cancel };
  const runQuick = (value: string) => {
    if (!token) {
      begin();
      return;
    }
    void command(value);
  };
  const kkuModels = (modelInfo?.models || []).filter((m: any) => m.backend === "kku");
  const visibleKkuModels = kkuModels.filter((m: any) => `${m.name || m.id} ${m.provider || ""}`.toLowerCase().includes(modelQuery.toLowerCase().trim()));
  const kkuInfo = modelInfo?.kku || {};
  const chooseKkuModel = async (model: any) => {
    setSwitchingModel(model.id);
    setModelNotice("");
    try {
      const current = await selectModel(model.id, "kku");
      setModelInfo((previous: any) => ({ ...previous, current }));
      setModelNotice(`เลือก ${model.name || model.id} แล้ว · ใช้ใน Chat และคำถามทั่วไปใน Operator`);
    } catch (error: any) {
      setModelNotice(error.message || "เปลี่ยนโมเดลไม่สำเร็จ");
    } finally {
      setSwitchingModel("");
    }
  };
  const overview = [
    [
      "◉",
      "AI Core",
      online ? modelInfo?.current?.status || "Unknown" : "Status unavailable",
    ],
    [
      "◎",
      "Memory",
      token && grants.includes("memory") ? "Search allowed" : "Not allowed",
    ],
    ["♩", "Voice", voiceOn.current ? "Mic active" : "Mic off"],
    ["◇", "Workspace", panel],
    [
      "⬡",
      "Runtime",
      online ? modelInfo?.current?.backend || "Unknown" : "Unavailable",
    ],
    [
      "⌘",
      "Session",
      token ? grants.length + " permissions" : "Session not started",
    ],
  ];
  return (
    <main className={"operator " + view}>
      <header className="op-header">
        <div className="op-health">
          <i className={online ? "live" : ""} />
          <span>
            SYSTEM STATUS <b>{online ? "ONLINE" : "UNAVAILABLE"}</b>
          </span>
        </div>
        <div className="op-clock">
          <small>
            {now.toLocaleDateString("en-GB", {
              weekday: "long",
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </small>
          <time>{now.toLocaleTimeString("en-GB")}</time>
        </div>
        <button
          className="op-session"
          onClick={() => (token ? stop() : begin())}
        >
          {token ? "End session / revoke access" : "Start session"} <span>◎</span>
        </button>
      </header>
      <div className="op-title">
        <div>
          <small>AIRIS UNIVERSAL AI</small>
          <h1>Command Center</h1>
        </div>
        <span>
          OPERATOR MODE <i /> {state}
        </span>
      </div>
      <div className="op-grid">
        <section className="op-card op-overview">
          <h2>AI CORE OVERVIEW</h2>
          {overview.map(([icon, title, value]) => (
            <div className="op-stat" key={title}>
              <span className="op-icon">{icon}</span>
              <div>
                <b>{title}</b>
                <small>{value}</small>
              </div>
            </div>
          ))}
        </section>
        <section className="op-card op-hero">
          <div className="op-hero-top">
            <span>NEURAL INTERFACE</span>
            <span>
              {view === "camera" ? "CAMERA VIEW" : "CORE VISUALIZATION"}
            </span>
          </div>
          <video
            ref={video}
            muted
            playsInline
            className="operator-camera"
            style={{ display: view === "camera" ? "block" : "none" }}
          />
          <canvas
            ref={canvas}
            className="operator-hands"
            style={{ display: view === "camera" ? "block" : "none" }}
          />
          {view === "core" && <OperatorCore state={state} level={level} />}
          <div className="op-hero-bottom">
            <span>
              <i className={voiceOn.current ? "live" : ""} />
              {voiceOn.current ? "MIC ACTIVE" : "MIC OFF"}
            </span>
            <span>{token ? "SESSION AUTHORIZED" : "AWAITING PERMISSION"}</span>
          </div>
        </section>
        <section className="op-card op-feed">
          <h2>
            LIVE ACTIVITY{" "}
            <span>{entries.length ? "SESSION" : "NO EVENTS"}</span>
          </h2>
          <div className="op-events">
            {entries.length ? (
              entries
                .slice(-5)
                .reverse()
                .map((e, i) => (
                  <article key={i}>
                    <small>
                      {e.at} · {e.source}
                    </small>
                    <p>{e.text}</p>
                  </article>
                ))
            ) : (
              <div className="op-empty">
                <span>⌁</span>
                <p>No activity yet</p>
                <small>
                  Commands and results will appear here
                  <br />
                  after the session starts
                </small>
              </div>
            )}
          </div>
        </section>
        <section className="op-card op-workspaces">
          <h2>
            AGENT WORKSPACES <span>SELECT PANEL</span>
          </h2>
          <nav className="operator-panels">
            {panels.map((p, i) => (
              <button
                data-gesture
                className={p === panel ? "selected" : ""}
                key={p}
                onClick={() => setPanel(p)}
              >
                <span className="op-icon">{["⌘", "⌕", "☷", "◎"][i]}</span>
                <span>
                  {p}
                  <small>
                    {p === panel ? "Selected workspace" : "Standby panel"}
                  </small>
                </span>
              </button>
            ))}
          </nav>
          <small className="op-note">
            Panels organize commands; they are not separate background agents.
          </small>
        </section>
        <section className="op-card op-quick">
          <h2>QUICK COMMANDS</h2>
          <button data-gesture onClick={() => runQuick("list apps")}>
            ⌘ <span>Show installed apps</span> ↗
          </button>
          <button
            data-gesture
            onClick={() => {
              if (!token) begin();
              else if (voiceOn.current) stopMic();
              else void listen();
            }}
          >
            ♩ <span>{voiceOn.current ? "Stop listening" : "Start listening"}</span> ↗
          </button>
          <button
            data-gesture
            onClick={() => {
              if (!token) begin();
              else if (view === "camera") stopCamera();
              else void switchCamera();
            }}
          >
            ◉{" "}
            <span>
              {view === "camera" ? "Return to AI Core" : "Open camera / gestures"}
            </span>{" "}
            ↗
          </button>
          <button
            onClick={() => {
              setText("search web ");
              document.getElementById("operator-command")?.focus();
            }}
          >
            ⌕ <span>Search web with sources</span> ↗
          </button>
        </section>
        <section className="op-card op-monitor">
          <h2>SESSION MONITOR</h2>
          <div className="op-meters">
            {[
              [
                online ? String(systemInfo?.websocket_clients ?? "—") : "—",
                "Chat clients",
              ],
              [
                String(entries.filter((e) => e.source === "you").length),
                "Commands",
              ],
              [token ? String(grants.length) : "0", "Permissions"],
            ].map(([value, label]) => (
              <div key={label}>
                <div className="op-ring">{value}</div>
                <small>{label}</small>
              </div>
            ))}
          </div>
          <small>Values from this server and session · CPU / RAM unavailable</small>
        </section>
        <section className="op-card op-models">
          <h2>
            ACTIVE MODEL <span>{online ? "SERVER REPORTED" : "OFFLINE"}</span>
          </h2>
          <div className="op-model-current">
            <span className="op-icon">⬡</span>
            <div>
              <b>{modelInfo?.current?.model || "Waiting for server"}</b>
              <small>
                {online
                  ? modelInfo?.current?.backend +
                    " · " +
                    modelInfo?.current?.status
                  : "Latest status unavailable"}
              </small>
            </div>
          </div>
          <div className="op-model-list">
            {(modelInfo?.models || [])
              .filter((m: any) => m.backend === "ollama")
              .map((m: any) => (
                <span key={m.id} title={m.description}>
                  {m.name}
                  <small>
                    {m.installed ? "Installed locally" : "Not found / unavailable"}
                  </small>
                </span>
              ))}
          </div>
          <small>รายการด้านบนคือโมเดลที่ติดตั้งผ่าน Ollama</small>
        </section>
        <section className="op-card op-kku-limits">
          <h2>
            KKU API / TOKEN LIMITS &amp; CAPABILITIES
            <span className={kkuInfo.configured ? "op-online" : "op-offline"}>
              {kkuInfo.configured ? "KEY CONFIGURED" : "KEY NOT CONFIGURED"}
            </span>
          </h2>
          <div className="op-kku-summary">
            <div><b>Airis output ceiling</b><strong>{tokenLabel(kkuInfo.airis_output_tokens)} tokens</strong></div>
            <div><b>Long context handling</b><strong>{tokenLabel(kkuInfo.airis_context_chars)} chars</strong></div>
            <div><b>Usage / quota</b><strong>{kkuInfo.observed_models ? `${kkuInfo.observed_models} โมเดล · ข้อมูลจากการใช้งาน` : "ยังไม่มีข้อมูล"}</strong></div>
            <div><b>Image generation</b><strong>{imageInfo === null ? "กำลังตรวจสอบ" : imageInfo.available ? "Airis local FLUX" : "ไม่พร้อมบนเครื่องนี้"}</strong></div>
          </div>
          <p className="op-note">
            ค่า context/output ด้านล่างมาจาก KKU model catalogue เมื่อมีข้อมูล; ค่า Airis เป็นเพดานคำขอที่ระบบใช้จริง
            และโควตาจะอัปเดตจาก response ล่าสุดของ KKU หลังใช้งานจริง · ค้นเว็บ/สร้างเว็บทำผ่านความสามารถของ Airis
            ส่วนสร้างภาพใช้ Airis local FLUX และเอกสาร/ภาพแนบอ่านผ่าน OCR ก่อนส่งข้อความเข้าโมเดล
          </p>
          <div className="op-kku-toolbar">
            <input type="search" aria-label="ค้นหาโมเดล KKU" placeholder={`ค้นหา ${kkuModels.length} โมเดล หรือผู้ให้บริการ…`} value={modelQuery} onChange={(event) => setModelQuery(event.target.value)} />
            <button onClick={() => void refreshModels.current()} disabled={refreshingModels}>{refreshingModels ? "กำลังอัปเดต…" : "รีเฟรชโควตา"}</button>
          </div>
          {(modelNotice || modelStatusError) && <p role="status" className="op-note">{modelStatusError || modelNotice}</p>}
          {kkuModels.length ? (
            <div className="op-kku-models">
              {visibleKkuModels.map((m: any) => {
                const caps = m.capabilities || {};
                const limits = m.limits || {};
                const selected = modelInfo?.current?.backend === "kku" && modelInfo?.current?.model === m.id;
                return (
                  <article className={`op-kku-model${selected ? " selected" : ""}`} key={m.id}>
                    <header>
                      <span className="op-kku-icon">{m.icon || "☁"}</span>
                      <div><b>{m.name || m.id}</b><small>{m.provider || "KKU"} · {m.installed ? "อยู่ในรายการ KKU" : "ต้องตั้ง API key"}</small></div>
                    </header>
                    <div className="op-kku-tokens">
                      <span><small>Context</small><b>{tokenLabel(limits.context_window)}</b></span>
                      <span><small>Max output</small><b>{tokenLabel(limits.max_output_tokens)}</b></span>
                      <span><small>Airis request</small><b>{tokenLabel(limits.airis_output_tokens)}</b></span>
                    </div>
                    <QuotaDetails observed={m.observed} />
                    <div className="op-capabilities" aria-label={`ความสามารถ ${m.name || m.id}`}>
                      {Object.entries(caps).filter(([, enabled]) => enabled === true).map(([key]) => (
                        <span key={key} className="available">
                          {capabilityLabel(key)}
                        </span>
                      ))}
                      <span className="via-airis">สร้างภาพผ่าน Airis: {imageInfo === null ? "กำลังตรวจสอบ" : imageInfo.available ? "FLUX" : "ไม่พร้อม"}</span>
                    </div>
                    <button className="op-select-model" aria-pressed={selected} onClick={() => void chooseKkuModel(m)} disabled={selected || !m.installed || !online || !!switchingModel || state === "Thinking"}>{selected ? "กำลังใช้งาน" : switchingModel === m.id ? "กำลังเลือก…" : "ใช้โมเดลนี้"}</button>
                  </article>
                );
              })}
              {!visibleKkuModels.length && <p className="op-kku-empty">ไม่พบโมเดลที่ตรงกับคำค้น</p>}
            </div>
          ) : (
            <div className="op-kku-empty">ยังไม่พบรายการโมเดล KKU · ตั้ง <code>KKU_API_KEY</code> และกด refresh เพื่อโหลดรายการ</div>
          )}
          <small className="op-kku-endpoint">
            Catalog: {kkuInfo.catalog_endpoint || "https://gen.ai.kku.ac.th/api/v1/models"} · Last observed: {kkuInfo.observed_updated_at ? new Date(kkuInfo.observed_updated_at * 1000).toLocaleString() : "ยังไม่มีการเรียกใช้งาน"}
          </small>
        </section>
        <section
          data-gesture
          className="op-card operator-panel"
          style={{ transform: `translate(${offset.x}px,${offset.y}px)` }}
        >
          <h2>
            {panel.toUpperCase()} / COMMAND OUTPUT{" "}
            <button onClick={() => setOffset({ x: 0, y: 0 })}>
              Reset position
            </button>
          </h2>
          <div className="op-output">
            {!results.length && !entries.length && (
              <p className="op-note">
                Start a session, type a command, or enable the microphone to talk to Airis.
              </p>
            )}
            {results.map((r, i) => (
              <article key={i}>
                <b>{r.title}</b>
                <p>{r.content}</p>
                {r.url && /^https?:\/\//.test(r.url) && (
                  <a href={r.url} target="_blank" rel="noreferrer">
                    Open source ↗
                  </a>
                )}
                <small>
                  {r.source} · {r.timestamp || "No timestamp"}
                </small>
              </article>
            ))}
            <div className="operator-transcript" aria-live="polite">
              {entries.map((e, i) => (
                <p key={i}>
                  <small>
                    {e.at} · {e.source}
                  </small>
                  {e.text}
                </p>
              ))}
            </div>
          </div>
        </section>
      </div>
      <div className="operator-controls">
        <button disabled={starting} onClick={forget}>
          Change / forget saved permissions
        </button>
        <select
          aria-label="Camera facing"
          value={facing}
          disabled={view === "camera"}
          onChange={(e) => setFacing(e.target.value)}
        >
          <option value="user">Front camera</option>
          <option value="environment">Rear camera</option>
        </select>
        <p className="operator-feedback">
          {gesture ||
            "Palm 1s → Listen · Pinch → Select / drag · Swipe → Panel · Fist → Cancel"}
        </p>
        <button data-gesture onClick={cancel} disabled={!token}>
          Stop response / speech
        </button>
      </div>
      <footer className="op-command-bar">
        <button
          className={"op-talk " + (voiceOn.current ? "listening" : "")}
          onClick={() => {
            if (!token) begin();
            else if (voiceOn.current) stopMic();
            else void listen();
          }}
        >
          <div className="operator-wave" aria-label="Microphone level">
            {Array.from({ length: 16 }, (_, i) => (
              <i
                key={i}
                style={{
                  height: 4 + level * (12 + 18 * Math.abs(Math.sin(i))),
                }}
              />
            ))}
          </div>
          <span>
            TALK TO AIRIS
            <small>
              {voiceOn.current ? "Listening enabled" : "Tap to start"}
            </small>
          </span>
        </button>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!token) {
              begin();
              return;
            }
            if (text.trim()) {
              void command(text);
              setText("");
            }
          }}
        >
          <input
            id="operator-command"
            aria-label="Operator command"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Search web … / Open app … / Read file …"
          />
          <button>Send command ↗</button>
        </form>
      </footer>
      {!token && permissionOpen && (
        <dialog
          ref={permissionDialog}
          className="op-permission-backdrop"
          onCancel={(e) => {
            if (starting) e.preventDefault();
            else setPermissionOpen(false);
          }}
          aria-label="Airis session permissions"
        >
          <section className="operator-permissions">
            <button
              className="permission-close"
              disabled={starting}
              aria-label="Close permissions"
              onClick={() => setPermissionOpen(false)}
            >
              ×
            </button>
            <small>SESSION PERMISSIONS</small>
            <h2>Start Airis session</h2>
            <p>
              Your choices are remembered for this site and can be changed at any time.
              macOS permissions and high-risk actions still require confirmation.
            </p>
            {[
              ["voice", "Microphone and speech"],
              ["camera", "Camera and hand gestures"],
              [
                "files",
                "Access files within an approved folder (default: user folder)",
              ],
              ["web", "Search the web with source links"],
              ["memory", "Search Airis memory"],
              ["system", "Open installed apps under macOS permissions"],
              ["location", "Location for weather and context"],
              ["environment", "Analyze camera scenes when requested"],
              ["telemetry", "CPU, GPU, and system status"],
              ["pointer", "Control the pointer only when manually enabled"],
            ].map(([id, label]) => (
              <label key={id}>
                <input
                  type="checkbox"
                  checked={grants.includes(id)}
                  onChange={(e) =>
                    setGrants((g) =>
                      e.target.checked ? [...g, id] : g.filter((x) => x !== id),
                    )
                  }
                />
                {label}
              </label>
            ))}
            {grants.includes("files") && (
              <input
                aria-label="Approved folder"
                value={root}
                onChange={(e) => setRoot(e.target.value)}
                placeholder="Leave blank for the user folder, or use / for all locations allowed by macOS"
              />
            )}
            {sessionError && <p role="alert">{sessionError}</p>}
            <button disabled={starting} onClick={start}>
              {starting ? "Starting session…" : "Approve selected permissions and start"}
            </button>
          </section>
        </dialog>
      )}
    </main>
  );
}
