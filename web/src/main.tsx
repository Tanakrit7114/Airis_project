import Operator from "./pages/Operator";
import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";
import Sidebar from "./components/Sidebar";
import Icon from "./components/Icon";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Extensions from "./pages/Extensions";
import { createSession, getSessions } from "./api/client";

function App() {
  const [page, setPage] = useState(
    location.hash === "#extensions" ? "extensions" : "chat",
  );
  const [sessions, setSessions] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    let live = true;
    const refresh = () =>
      getSessions()
        .then((x) => {
          if (live) setSessions(x);
        })
        .catch(() => {});
    refresh();
    const timer = setInterval(refresh, 5000);
    return () => {
      live = false;
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setSidebarOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, []);

  const newChat = () =>
    createSession()
      .then((session) => {
        setSessions((current) => [
          session,
          ...current.filter((item) => item.id !== session.id),
        ]);
        setSessionId(session.id);
        setPage("chat");
      })
      .catch(() => {});

  const select = (id: string) => {
    setSessionId(id);
    setPage("chat");
  };

  return (
    <div className={sidebarOpen ? "app sidebar-open" : "app"}>
      <button
        className="mobile-sidebar-toggle"
        aria-label="เปิดเมนู Airis"
        title="เปิดเมนู Airis"
        onClick={() => setSidebarOpen(true)}
      >
        <Icon name="menu" size={19} />
      </button>
      {sidebarOpen && (
        <button
          className="sidebar-backdrop"
          aria-label="ปิดเมนู Airis"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <Sidebar
        page={page}
        setPage={setPage}
        sessions={sessions}
        active={sessionId}
        onNew={newChat}
        onSelect={select}
        onClose={() => setSidebarOpen(false)}
      />
      {page === "operator" ? (
        <Operator />
      ) : page === "chat" ? (
        <Chat
          sessionId={sessionId}
          setSessionId={(id) => {
            setSessionId(id);
            getSessions().then(setSessions).catch(() => {});
          }}
        />
      ) : page === "dashboard" ? (
        <Dashboard />
      ) : (
        <Extensions />
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
