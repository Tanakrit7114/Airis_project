import Connectors from "../components/Connectors";
import React, { useEffect, useState } from "react";
import {
  getExtensions,
  getExtensionAuthUrl,
  disconnectExtension,
  testExtension,
  extensionAction,
} from "../api/client";
import Icon from "../components/Icon";
type Ext = {
  id: string;
  name: string;
  category: string;
  description: string;
  connected: boolean;
  capabilities: string[];
};
const iconName = (id: string) =>
  (
    ({
      gmail: "mail",
      drive: "folder",
      calendar: "calendar",
      github: "github",
      notion: "file",
    }) as Record<string, string>
  )[id] || "plug";
export default function Extensions() {
  const [items, setItems] = useState<Ext[]>([]),
    [busy, setBusy] = useState(""),
    [filter, setFilter] = useState(""),
    [notice, setNotice] = useState("");
  const load = () =>
    getExtensions()
      .then(setItems)
      .catch((e) => setNotice(e.message));
  useEffect(() => {
    load();
    const on = (e: MessageEvent) => {
      if (
        e.origin === location.origin &&
        e.data?.type === "jarvis-extension-connected"
      )
        load();
    };
    window.addEventListener("message", on);
    return () => window.removeEventListener("message", on);
  }, []);
  const connect = async (id: string) => {
    setBusy(id);
    setNotice("");
    try {
      const { authorize_url } = await getExtensionAuthUrl(id);
      window.open(
        authorize_url,
        "_blank",
        "noopener,noreferrer,width=720,height=820",
      );
      setNotice("Authorization window opened. Return here and run Test after approval.");
    } catch (e: any) {
      setNotice(e.message || "Could not connect");
    } finally {
      setBusy("");
    }
  };
  const disconnect = async (id: string) => {
    setBusy(id);
    try {
      await disconnectExtension(id);
      await load();
      setNotice("Disconnected");
    } catch (e: any) {
      setNotice(e.message);
    } finally {
      setBusy("");
    }
  };
  const test = async (id: string) => {
    setBusy(id);
    try {
      const r = await testExtension(id);
      setNotice(
        `${id}: connected and tested successfully${r.account ? " · account authorized" : ""}`,
      );
    } catch (e: any) {
      setItems((prev) =>
        prev.map((x) => (x.id === id ? { ...x, connected: false } : x)),
      );
      setNotice(
        `${id}: token is invalid or expired. Reconnect the account.`,
      );
    } finally {
      setBusy("");
    }
  };
  const demo = async (id: string) => {
    const actions: any = {
      gmail: ["recent", ""],
      drive: ["search", ""],
      calendar: ["upcoming", ""],
      github: ["repos", ""],
      notion: ["search", ""],
    };
    setBusy(id);
    try {
      const [a, q] = actions[id];
      const r = await extensionAction(id, a, q);
      setNotice(
        `${id}: data retrieved successfully · ${JSON.stringify(r).slice(0, 220)}…`,
      );
    } catch (e: any) {
      setItems((prev) =>
        prev.map((x) => (x.id === id ? { ...x, connected: false } : x)),
      );
      setNotice(`${id}: could not retrieve data. Reconnect the account.`);
    } finally {
      setBusy("");
    }
  };
  const shown = items.filter(
    (x) =>
      !filter ||
      `${x.name} ${x.category}`.toLowerCase().includes(filter.toLowerCase()),
  );
  return (
    <div className="extensions-page">
      <div className="extensions-head">
        <div>
          <div className="eyebrow">AIRIS / EXTENSIONS</div>
          <h1>Connect services</h1>
          <button onClick={() => load()}>Refresh status</button>
          <p>Connect an account, approve access, then run Test.</p>
        </div>
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Search services…"
        />
      </div>
      {notice && <div className="extension-notice">{notice}</div>}
      <div className="extension-grid">
        {shown.map((x) => (
          <article className="extension-card" key={x.id}>
            <div className="ext-top">
              <div className="ext-icon">
                <Icon name={iconName(x.id)} size={20} />
              </div>
              <div className="ext-title">
                <strong>{x.name}</strong>
                <span>{x.category}</span>
              </div>
              <div
                className={x.connected ? "ext-status connected" : "ext-status"}
              >
                {x.connected ? "Connected" : "Not connected"}
              </div>
            </div>
            <p>{x.description}</p>
            <div className="capabilities">
              {x.capabilities.map((c) => (
                <span key={c}>
                  <span>{c}</span>
                </span>
              ))}
            </div>
            <div className="ext-actions">
              {!x.connected ? (
                <button
                  className="primary"
                  onClick={() => connect(x.id)}
                  disabled={busy === x.id}
                >
                  {busy === x.id ? "Opening…" : "Connect account"}
                </button>
              ) : (
                <>
                  <button onClick={() => test(x.id)} disabled={busy === x.id}>
                    Test
                  </button>
                  <button onClick={() => demo(x.id)} disabled={busy === x.id}>
                    Try data access
                  </button>
                  <button
                    className="danger"
                    onClick={() => connect(x.id)}
                    disabled={busy === x.id}
                  >
                    Reconnect
                  </button>
                </>
              )}
            </div>
          </article>
        ))}
      </div>
      <Connectors />
      <section className="extension-setup">
        <h2>Setup</h2>
        <p>
          A connection is usable only after Test succeeds. Reconnect the account
          if Test fails.
        </p>
        <pre>{`GOOGLE_CLIENT_ID=\nGOOGLE_CLIENT_SECRET=\nGITHUB_CLIENT_ID=\nGITHUB_CLIENT_SECRET=\nNOTION_CLIENT_ID=\nNOTION_CLIENT_SECRET=`}</pre>
      </section>
    </div>
  );
}
