import React, { useEffect, useRef, useState } from "react";
import Icon from "./Icon";
type Props = {
  page: string;
  setPage: (p: string) => void;
  sessions: any[];
  active: string | null;
  onNew: () => void;
  onSelect: (id: string) => void;
  onClose?: () => void;
};
export default function Sidebar({
  page,
  setPage,
  sessions,
  active,
  onNew,
  onSelect,
  onClose,
}: Props) {
  const [query, setQuery] = useState("");
  const searchRef = useRef<HTMLInputElement | null>(null);
  const onNewRef = useRef(onNew);
  onNewRef.current = onNew;
  useEffect(() => {
    const onShortcut = (event: KeyboardEvent) => {
      if (!(event.metaKey || event.ctrlKey)) return;
      const key = event.key.toLowerCase();
      if (key === "k") {
        event.preventDefault();
        searchRef.current?.focus();
      } else if (key === "o" && event.shiftKey) {
        event.preventDefault();
        onNewRef.current();
        onClose?.();
      }
    };
    window.addEventListener("keydown", onShortcut);
    return () => window.removeEventListener("keydown", onShortcut);
  }, [onClose]);
  const normalizedQuery = query.trim().toLocaleLowerCase();
  const recent = normalizedQuery
    ? sessions.filter((session) =>
        String(session.title || "New conversation")
          .toLocaleLowerCase()
          .includes(normalizedQuery),
      )
    : sessions;
  const navigate = (next: string) => {
    setPage(next);
    onClose?.();
  };
  return (
    <aside className="sidebar">
      <div className="sidebar-topbar">
        <div className="brand">
          <div className="orb">
            <Icon name="zap" size={17} />
          </div>
          <div>
            <strong>Airis</strong>
            <span>Universal AI</span>
          </div>
        </div>
        <button
          className="sidebar-close"
          aria-label="ปิดเมนู"
          title="ปิดเมนู"
          onClick={onClose}
        >
          <Icon name="close" size={18} />
        </button>
      </div>
      <button
        className="new-chat"
        aria-keyshortcuts="Meta+Shift+O Control+Shift+O"
        onClick={() => {
          onNew();
          onClose?.();
        }}
      >
        <Icon name="plus" size={16} /> <span>New chat</span>
        <kbd>⌘ ⇧ O</kbd>
      </button>
      <nav aria-label="Primary navigation">
        <button
          className={page === "operator" ? "active" : ""}
          onClick={() => navigate("operator")}
        >
          <Icon name="zap" size={16} />
          Operator
        </button>
        <button
          className={page === "chat" ? "active" : ""}
          onClick={() => navigate("chat")}
        >
          <Icon name="message" size={16} />
          Chat
        </button>
        <button
          className={page === "dashboard" ? "active" : ""}
          onClick={() => navigate("dashboard")}
        >
          <Icon name="dashboard" size={16} />
          Dashboard
        </button>
        <button
          className={page === "extensions" ? "active" : ""}
          onClick={() => navigate("extensions")}
        >
          <Icon name="plug" size={16} />
          Extensions
        </button>
      </nav>
      {page === "chat" && (
        <div className="history">
          <div className="history-head">
            <div className="label">RECENT</div>
            <span>{normalizedQuery ? `${recent.length}/${sessions.length}` : recent.length}</span>
          </div>
          <div className="history-search">
            <Icon name="search" size={14} />
            <input
              ref={searchRef}
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Escape") setQuery("");
              }}
              placeholder="Search chats"
              aria-label="ค้นหาประวัติแชต"
            />
            {query && (
              <button
                type="button"
                className="history-clear"
                onClick={() => setQuery("")}
                aria-label="ล้างการค้นหา"
                title="ล้างการค้นหา"
              >
                <Icon name="close" size={13} />
              </button>
            )}
          </div>
          {recent.length === 0 && (
            <p className="history-empty">
              {sessions.length ? "ไม่พบแชตที่ค้นหา" : "ยังไม่มีประวัติแชต"}
            </p>
          )}
          {recent.map((s, index) => (
            <button
              key={s.id}
              title={s.title || "New chat"}
              className={active === s.id ? "session active" : "session"}
              onClick={() => {
                onSelect(s.id);
                onClose?.();
              }}
            >
              <b>{index + 1}</b>
              <span>
                {s.title || "New chat"}
                <small>
                  {s.updated_at
                    ? new Date(
                        s.updated_at.replace(" ", "T") + "Z",
                      ).toLocaleString("en-GB", {
                        day: "numeric",
                        month: "short",
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : ""}
                </small>
              </span>
            </button>
          ))}
        </div>
      )}
      <div className="sidebar-footer">Local-first · Adaptive runtime</div>
    </aside>
  );
}
