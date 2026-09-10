import React, { useEffect, useRef, useState } from "react";
import Icon from "../components/Icon";
import {
  connectChat,
  getSession,
  uploadDocument,
  mergePdfs,
  getModels,
  selectModel,
} from "../api/client";
import MessageBubble from "../components/MessageBubble";
import TypingIndicator from "../components/TypingIndicator";
import ExtensionResult from "../components/ExtensionResult";
import { hydrateMessage, updateResponse } from "../chatState";
import "../chatFixes.css";

type Attachment = {
  id: string;
  filename: string;
  text?: string;
  pages?: number;
  engine: string;
  reused?: boolean;
  mergedFrom?: string[];
};
export default function Chat({
  sessionId,
  setSessionId,
}: {
  sessionId: string | null;
  setSessionId: (id: string) => void;
}) {
  const [messages, setMessages] = useState<any[]>([]),
    [input, setInput] = useState(""),
    [status, setStatus] = useState("Ready"),
    [typing, setTyping] = useState(false),
    [streaming, setStreaming] = useState(false),
    [confirm, setConfirm] = useState<any>(null),
    [attachment, setAttachment] = useState<Attachment | null>(null),
    [uploading, setUploading] = useState(false),
    [models, setModels] = useState<any[]>([]),
    [currentModel, setCurrentModel] = useState<any>(null),
    [switching, setSwitching] = useState(false);
  const [coding, setCoding] = useState(false);
  const ws = useRef<WebSocket | null>(null),
    fileRef = useRef<HTMLInputElement | null>(null),
    textRef = useRef<HTMLTextAreaElement | null>(null);
  const active = useRef<string | null>(null),
    assignedSession = useRef<string | null>(sessionId),
    stopping = useRef(false);
  const [busy, setBusy] = useState(false),
    [connected, setConnected] = useState(false),
    [loading, setLoading] = useState(false),
    [showLatest, setShowLatest] = useState(false);
  const listRef = useRef<HTMLDivElement | null>(null),
    followBottom = useRef(true),
    draft = useRef(input);
  draft.current = input;
  useEffect(() => {
    let live = true;
    const refresh = () =>
      getModels()
        .then((x) => {
          if (!live) return;
          setModels(x.models || []);
          setCurrentModel(x.current);
        })
        .catch(() => {});
    refresh();
    const timer = setInterval(refresh, 60000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, []);
  useEffect(() => {
    let disposed = false,
      retry: ReturnType<typeof setTimeout> | undefined;
    active.current = null;
    stopping.current = false;
    assignedSession.current = sessionId;
    setBusy(false);
    setTyping(false);
    setStreaming(false);
    setConfirm(null);
    setAttachment(null);
    setMessages([]);
    setLoading(!!sessionId);
    followBottom.current = true;
    if (sessionId)
      getSession(sessionId)
        .then((x) => {
          if (!disposed) setMessages((x.messages || []).map(hydrateMessage));
        })
        .catch(() => {
          if (!disposed)
            setStatus("Could not load history. Please reopen this chat.");
        })
        .finally(() => {
          if (!disposed) setLoading(false);
        });
    const finish = () => {
      active.current = null;
      setBusy(false);
      setTyping(false);
      setStreaming(false);
      setConfirm(null);
    };
    const open = () => {
      if (disposed) return;
      const socket = connectChat(
        (data) => {
          if (disposed || !active.current) return;
          if (data.session_id) assignedSession.current = data.session_id;
          if (data.type === "status") setStatus(data.label || data.status);
          if (data.type === "model_status") setCurrentModel(data);
          if (data.type === "typing") setTyping(!!data.active);
          if (data.type === "confirmation_request") {
            setConfirm(data);
            setTyping(false);
            setStreaming(false);
          }
          if (data.type === "token") {
            setTyping(false);
            setStreaming(true);
          }
          if (
            ["token", "image", "extension_result", "done", "error"].includes(
              data.type,
            )
          ) {
            const id = active.current;
            setMessages((m) => updateResponse(m, id, data));
          }
          if (data.type === "done" || data.type === "error") {
            finish();
            setStatus(data.type === "done" ? "Ready" : "Error");
            setAttachment(null);
            if (assignedSession.current) setSessionId(assignedSession.current);
          }
        },
        () => {
          if (!disposed) {
            setConnected(true);
            setStatus("Ready");
          }
        },
        () => {
          if (!disposed) setStatus("Connection problem");
        },
      );
      ws.current = socket;
      socket.onclose = () => {
        if (disposed) return;
        setConnected(false);
        const manuallyStopped = stopping.current;
        stopping.current = false;
        if (manuallyStopped) {
          setStatus("Stopped");
          retry = setTimeout(open, 2000);
          return;
        }
        if (active.current) {
          const id = active.current;
          setMessages((m) =>
            updateResponse(m, id, {
              type: "error",
              message:
                "Connection lost. Reopen chat history to check the result before sending again.",
            }),
          );
          finish();
        }
        setStatus("Reconnecting…");
        retry = setTimeout(open, 2000);
      };
    };
    open();
    return () => {
      disposed = true;
      clearTimeout(retry);
      ws.current?.close();
      active.current = null;
    };
  }, [sessionId]);
  useEffect(() => {
    let live = true;
    const refresh = async () => {
      if (!sessionId || active.current) return;
      try {
        const result = await getSession(sessionId);
        if (live && !active.current)
          setMessages((result.messages || []).map(hydrateMessage));
      } catch {}
    };
    const timer = setInterval(refresh, 5000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, [sessionId]);
  useEffect(() => {
    const list = listRef.current;
    if (list && followBottom.current) list.scrollTop = list.scrollHeight;
  }, [messages, typing]);
  useEffect(() => {
    const textarea = textRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 180)}px`;
  }, [input]);
  const send = () => {
    const text = input.trim();
    if (!text || active.current || switching || uploading || loading) return;
    if (ws.current?.readyState !== WebSocket.OPEN) {
      setStatus("Not connected. Your message remains in the composer.");
      return;
    }
    const id = crypto.randomUUID();
    active.current = id;
    stopping.current = false;
    setBusy(true);
    followBottom.current = true;
    setMessages((m) => [
      ...m,
      {
        id: crypto.randomUUID(),
        role: "user",
        content: text,
        attachment: attachment?.filename,
        attachmentDownloadUrl: attachment?.id
          ? `/api/documents/${encodeURIComponent(attachment.id)}/download`
          : undefined,
        done: true,
      },
      { id, role: "assistant", content: "", done: false },
    ]);
    try {
      ws.current.send(
        JSON.stringify({
          text,
          mode: coding ? "coding" : "chat",
          allow_cloud: true,
          session_id: assignedSession.current,
          document_id: attachment?.id || null,
          document_text: attachment?.text || "",
          attachment_filename: attachment?.filename || null,
        }),
      );
      setInput("");
      setTyping(true);
      setStreaming(false);
      setStatus("Thinking…");
    } catch {
      setMessages((m) =>
        updateResponse(m, id, {
          type: "error",
          message: "Could not send. Please try again.",
        }),
      );
      active.current = null;
      setBusy(false);
    }
  };
  const stop = () => {
    const id = active.current;
    if (!id) return;
    stopping.current = true;
    active.current = null;
    setMessages((m) =>
      m.map((message) =>
        message.id === id
          ? {
              ...message,
              done: true,
              stopped: true,
              content: message.content
                ? `${message.content}\n\nResponse stopped.`
                : "Response stopped.",
            }
          : message,
      ),
    );
    setBusy(false);
    setTyping(false);
    setStreaming(false);
    setConfirm(null);
    setStatus("Stopped");
    ws.current?.close(1000, "generation stopped");
  };
  const confirmAction = (approved: boolean) => {
    if (ws.current?.readyState !== WebSocket.OPEN || !confirm) return;
    ws.current.send(
      JSON.stringify({
        type: "confirmation",
        session_id: confirm.session_id,
        approved,
      }),
    );
    setConfirm(null);
    setTyping(approved);
    setStatus(approved ? "Working…" : "Cancelled");
  };
  const isPdf = (file: File) =>
    file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

  const upload = async (file: File) => {
    setUploading(true);
    setStatus("Reading document / OCR…");
    try {
      setAttachment(await uploadDocument(file, true));
      setStatus("Document ready");
    } catch (e) {
      setStatus("Upload failed");
      alert(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };
  const uploadFiles = async (files: File[]) => {
    if (files.length === 1) {
      await upload(files[0]);
      return;
    }
    if (!files.every(isPdf)) {
      setStatus("เลือกหลายไฟล์ได้เฉพาะ PDF");
      alert("เมื่อเลือกหลายไฟล์ กรุณาเลือกเฉพาะ PDF เพื่อให้ Airis รวมไฟล์อัตโนมัติ");
      return;
    }
    setUploading(true);
    setStatus(`กำลังรวม PDF ${files.length} ไฟล์ แล้วอ่านเอกสาร…`);
    try {
      const merged = await mergePdfs(files);
      const mergedFile = new File([merged], "airis-merged.pdf", {
        type: "application/pdf",
      });
      const indexed = await uploadDocument(mergedFile, true);
      setAttachment({
        ...indexed,
        filename: "airis-merged.pdf",
        mergedFrom: files.map((file) => file.name),
      });
      setStatus(`รวม PDF และอ่านเอกสารแล้ว · ${files.length} ไฟล์`);
    } catch (error) {
      setStatus("รวม PDF ไม่สำเร็จ");
      alert(error instanceof Error ? error.message : "รวม PDF ไม่สำเร็จ");
    } finally {
      setUploading(false);
    }
  };
  const changeModel = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const item = models.find((x) => `${x.backend}:${x.id}` === e.target.value);
    if (!item || (item.id === currentModel?.model && item.backend === currentModel?.backend)) return;
    setSwitching(true);
    setStatus("Loading model…");
    try {
      const r = await selectModel(item.id, item.backend);
      setCurrentModel(r);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Could not switch model");
    } finally {
      setSwitching(false);
      setStatus("Ready");
    }
  };
  const modelGroups = [
    ["kku", "☁ KKU Cloud"],
    ["ollama", "⬡ Ollama Local"],
    ["mlx", "◆ MLX Local"],
    ["llama.cpp", "▣ GGUF Local"],
  ] as const;
  const selectedModel = models.find(
    (m) => m.id === currentModel?.model && m.backend === currentModel?.backend,
  );
  const modelIcon = selectedModel?.icon || (currentModel?.backend === "kku" ? "☁" : "⬡");
  const statusTone = /error|problem|failed/i.test(status)
    ? "error"
    : /stop|cancel/i.test(status)
      ? "stopped"
      : /reconnect|connect/i.test(status)
        ? "connecting"
        : /think|work|load|read|upload|merge/i.test(status)
          ? "working"
          : "ready";
  return (
    <main className="chat-page">
      <header>
        <div>
          <div className="eyebrow">AIRIS / CHAT</div>
          <h1>Airis Universal AI</h1>
          <div className="model-badge">
            <span aria-hidden="true">{modelIcon}</span>{" "}
            {currentModel?.model || "Loading model…"} ·{" "}
            {currentModel?.backend || "auto"}
          </div>
        </div>
        <div className="header-controls">
          <label className="model-select">
            <span>Main model</span>
            <Icon name="chevron" size={14} />
            <select
              value={currentModel ? `${currentModel.backend}:${currentModel.model}` : ""}
              onChange={changeModel}
              disabled={switching || busy}
            >
              <option value="" disabled>
                Select model
              </option>
              {modelGroups.map(([backend, label]) => {
                const choices = models.filter((m: any) => m.backend === backend);
                return choices.length ? (
                  <optgroup key={backend} label={label}>
                    {choices.map((m: any) => (
                      <option
                        key={`${m.backend}:${m.id}`}
                        value={`${m.backend}:${m.id}`}
                        disabled={!m.installed}
                      >
                        {m.icon || (m.backend === "kku" ? "☁" : "⬡")} {m.name}
                        {m.provider ? ` · ${m.provider}` : ""}
                        {!m.installed
                          ? m.backend === "kku"
                            ? " — API key required"
                            : " — not installed"
                          : ""}
                      </option>
                    ))}
                  </optgroup>
                ) : null;
              })}
            </select>
          </label>
          <div className={`status status-${statusTone}`} role="status" aria-live="polite">
            <span className="dot" />
            {switching ? (
              <>
                <span className="spin-icon">
                  <Icon name="loader" size={14} />
                </span>
                Loading model…
              </>
            ) : (
              status
            )}
          </div>
        </div>
      </header>
      <section className="chat-wrap">
        <div
          className="messages"
          ref={listRef}
          onScroll={() => {
            const list = listRef.current;
            if (list) {
              const atBottom =
                list.scrollHeight - list.scrollTop - list.clientHeight < 100;
              followBottom.current = atBottom;
              setShowLatest(!atBottom);
            }
          }}
        >
          {messages.length === 0 && (
            <div className="welcome">
              <div className="welcome-orb" />
              <h2>How can I help?</h2>
              <p>
                Ask about learning, research, documents, web information, or
                connected services.
              </p>
              <div className="chips">
                <button
                  onClick={() =>
                    setInput("Explain Machine Learning in simple terms")
                  }
                >
                  Explain a topic
                </button>
                <button onClick={() => setInput("Help me create a study plan")}>
                  Plan my studies
                </button>
                <button
                  onClick={() =>
                    setInput(
                      "Create an image of a futuristic university classroom",
                    )
                  }
                >
                  Create an image
                </button>
                <button
                  onClick={() =>
                    setInput("Research today's technology news with sources")
                  }
                >
                  Research with sources
                </button>
              </div>
            </div>
          )}
          {messages.map((m, i) => (
            <React.Fragment key={m.id || i}>
              {(m.content || m.done) && <MessageBubble m={m} />}
              {m.extensionResult && (
                <ExtensionResult result={m.extensionResult} />
              )}{" "}
              {m.image && (
                <div className="generated-image">
                  <img src={m.image} alt="Airis generated" />
                  <div className="image-actions">
                    <a href={m.image} target="_blank" rel="noreferrer">
                      Open image
                    </a>
                    <a href={m.image} download>
                      Save image
                    </a>
                  </div>
                </div>
              )}
            </React.Fragment>
          ))}
          {typing && (
            <div className="bubble-row assistant">
              <div className="avatar">A</div>
              <div className="bubble assistant typing-bubble">
                <div className="bubble-top">
                  <span>Airis</span>
                </div>
                <TypingIndicator />
              </div>
            </div>
          )}
          {streaming && !typing && <div className="stream-cursor" />}
          {showLatest && (
            <button
              className="scroll-latest"
              onClick={() => {
                const list = listRef.current;
                if (!list) return;
                followBottom.current = true;
                setShowLatest(false);
                list.scrollTo({ top: list.scrollHeight, behavior: "smooth" });
              }}
              aria-label="เลื่อนไปข้อความล่าสุด"
              title="เลื่อนไปข้อความล่าสุด"
            >
              <Icon name="chevron" size={15} />
            </button>
          )}
        </div>
        <div className="composer">
          {attachment && (
            <div className="attachment-bar">
              <span>
                {attachment.filename}
                {attachment.pages ? ` · ${attachment.pages} pages` : ""} ·{" "}
                {attachment.engine}
                {attachment.mergedFrom?.length
                  ? ` · รวมอัตโนมัติจาก ${attachment.mergedFrom.length} ไฟล์`
                  : ""}
              </span>
              {attachment.id ? (
                <a
                  href={`/api/documents/${encodeURIComponent(attachment.id)}/download`}
                  download={attachment.filename}
                  aria-label={`ดาวน์โหลด ${attachment.filename}`}
                >
                  {attachment.mergedFrom?.length ? "ดาวน์โหลด PDF รวม" : "ดาวน์โหลดไฟล์"}
                </a>
              ) : null}
              <button onClick={() => setAttachment(null)}>Remove</button>
            </div>
          )}
          <label
            className="composer-option"
            style={{ display: "block", fontSize: 12, marginBottom: 8 }}
          >
            <input
              type="checkbox"
              checked={coding}
              disabled={busy}
              onChange={(e) => setCoding(e.target.checked)}
            />{" "}
            Coding mode · รัน snippets ใน Docker ก่อนแสดง
          </label>
          <div className="composer-row">
            <input
              ref={fileRef}
              type="file"
              aria-label="เลือกไฟล์แนบ"
              multiple
              hidden
              onChange={(e) => {
                const files = Array.from(e.target.files || []);
                if (files.length) void uploadFiles(files);
                e.currentTarget.value = "";
              }}
            />
            <button
              className="icon-btn"
              aria-label="แนบไฟล์"
              onClick={() => fileRef.current?.click()}
              title="แนบไฟล์เดียว หรือเลือก PDF หลายไฟล์เพื่อรวมอัตโนมัติ"
              disabled={uploading || switching || busy || loading}
            >
              <Icon name="paperclip" size={18} />
            </button>
            <textarea
              ref={textRef}
              aria-label="ข้อความถึง Airis"
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (
                  e.key === "Enter" &&
                  !e.shiftKey &&
                  !e.nativeEvent.isComposing
                ) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Message Airis…"
              disabled={switching}
            />
            {busy ? (
              <button
                className="send-btn stop-btn"
                onClick={stop}
                aria-label="หยุดการตอบ"
                title="หยุดการตอบ"
              >
                <Icon name="stop" size={15} />
                <span>Stop</span>
              </button>
            ) : (
              <button
                className="send-btn"
                onClick={send}
                disabled={
                  uploading ||
                  switching ||
                  loading ||
                  !connected ||
                  !input.trim()
                }
              >
                <Icon name="send" size={16} />
                <span>Send</span>
              </button>
            )}
          </div>
        </div>
      </section>
      {confirm && (
        <div className="confirm-modal">
          <div className="confirm-card">
            <div className="eyebrow">CONFIRM ACTION</div>
            <h3>Confirm action</h3>
            <p>{confirm.description}</p>
            <div className="confirm-actions">
              <button onClick={() => confirmAction(false)}>Cancel</button>
              <button className="primary" onClick={() => confirmAction(true)}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
