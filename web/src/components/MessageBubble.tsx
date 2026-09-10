import React, { useState } from "react";
import MarkdownContent from "./MarkdownContent";
import Icon from "./Icon";
export default function MessageBubble({ m }: { m: any }) {
  const [copied, setCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);
  const copy = async () => {
    const value = m.content || "";
    try {
      if (navigator.clipboard?.writeText && window.isSecureContext) {
        await navigator.clipboard.writeText(value);
      } else {
        // Electron and older embedded web views can omit Clipboard API access.
        // Keep copy useful there with the same fallback used by many desktop
        // chat clients.
        const field = document.createElement("textarea");
        field.value = value;
        field.setAttribute("readonly", "");
        field.style.position = "fixed";
        field.style.opacity = "0";
        document.body.appendChild(field);
        try {
          field.select();
          if (!document.execCommand("copy")) throw new Error("copy failed");
        } finally {
          field.remove();
        }
      }
      setCopyFailed(false);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    } catch {
      setCopied(false);
      setCopyFailed(true);
      setTimeout(() => setCopyFailed(false), 1800);
    }
  };
  return (
    <div className={"bubble-row " + m.role}>
      <div className="avatar">
        {m.role === "assistant" ? (
          <Icon name="bot" size={15} />
        ) : (
          <Icon name="user" size={15} />
        )}
      </div>
      <div className={"bubble " + m.role}>
        <div className="bubble-top">
          <span>{m.role === "assistant" ? "Airis" : "You"}</span>
          {m.created_at && (
            <time>
              {new Date(m.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </time>
          )}
        </div>
        <MarkdownContent content={m.content || ""} />
        {m.role === "assistant" && m.content && (
          <button
            className="copy-btn"
            onClick={copy}
            title={copyFailed ? "Copy failed" : "Copy response"}
            aria-label={copyFailed ? "คัดลอกไม่สำเร็จ" : "คัดลอกคำตอบ"}
          >
            {copyFailed ? "Copy failed" : copied ? "Copied" : "Copy"}
            <Icon name={copied ? "check" : "copy"} size={13} />
          </button>
        )}
        {m.attachment && (
          <div className="attachment-mini">
            <Icon name="file" size={13} /> {m.attachment}
            {m.attachmentDownloadUrl && (
              <a href={m.attachmentDownloadUrl} download>
                ดาวน์โหลด
              </a>
            )}
          </div>
        )}
        {m.source && (
          <div className="badge">
            {m.source === "web"
              ? "Web search"
              : m.source === "file"
                ? "Saved document"
                : m.source === "extension"
                  ? "Extension"
                  : m.source === "kku"
                    ? "KKU Cloud"
                    : "Memory / general knowledge"}
          </div>
        )}
        {m.sources?.length > 0 && (
          <div className="source-list">
            {m.sources.map((s: any, i: number) => (
              <a
                key={i}
                href={s.url}
                target="_blank"
                rel="noreferrer"
                className="source-card"
              >
                <span className="source-main">
                  <img
                    className="source-card-favicon"
                    src={(() => {
                      try {
                        return new URL(s.url).origin + "/favicon.ico";
                      } catch {
                        return "";
                      }
                    })()}
                    onError={(e) => {
                      (e.currentTarget as HTMLImageElement).style.display =
                        "none";
                    }}
                    alt=""
                  />
                  {s.title || s.url}
                </span>
                <Icon name="external" size={12} />
                <small>{s.url}</small>
              </a>
            ))}
          </div>
        )}
        {m.persistent_documents?.length > 0 && (
          <div className="attachment-mini">
            <Icon name="file" size={13} />{" "}
            {Array.from(
              new Set(m.persistent_documents.map((d: any) => d.filename)),
            ).join(", ")}
          </div>
        )}
      </div>
    </div>
  );
}
