import React, { useEffect, useState } from "react";
export default function Connectors() {
  const [rows, setRows] = useState<any[]>([]),
    [name, setName] = useState(""),
    [url, setUrl] = useState(""),
    [notice, setNotice] = useState(""),
    [selected, setSelected] = useState<any>(null),
    [tools, setTools] = useState<any[]>([]),
    [tool, setTool] = useState(""),
    [args, setArgs] = useState("{}"),
    [busy, setBusy] = useState(false);
  const api = async (path: string, init: any = {}) => {
    const r = await fetch("/api/connectors" + path, init);
    const data = await r.json();
    if (!r.ok) throw Error(data.detail || "Connector error");
    return data;
  };
  const reload = () =>
    api("")
      .then(setRows)
      .catch((e) => setNotice(e.message));
  useEffect(() => {
    reload();
  }, []);
  const save = async (row: any) => {
    setBusy(true);
    try {
      await api("", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(row),
      });
      await reload();
      setNotice("Saved");
    } catch (e: any) {
      setNotice(e.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="extension-setup">
      <h2>MCP Connectors</h2>
      <p>
        Streamable HTTP · shared with Desktop · new connectors start disabled ·
        tools never run automatically
      </p>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          void save({ name, url, enabled: false });
        }}
      >
        <input
          required
          aria-label="Connector name"
          placeholder="Connector name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          required
          aria-label="MCP URL"
          placeholder="https://server.example/mcp"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button disabled={busy}>Add MCP server</button>
      </form>
      {rows.map((r) => (
        <div key={r.id}>
          <strong>{r.name}</strong> · {r.url}
          <button
            disabled={busy}
            onClick={() => void save({ ...r, enabled: !r.enabled })}
          >
            {r.enabled ? "Disable" : "Enable"}
          </button>
          <button
            disabled={!r.enabled || busy}
            onClick={async () => {
              setBusy(true);
              setTools([]);
              setTool("");
              try {
                const result = await api("/" + r.id + "/tools");
                setSelected(r);
                setTools(result.tools || []);
                setNotice("Tools discovered");
              } catch (e: any) {
                setNotice(e.message);
              } finally {
                setBusy(false);
              }
            }}
          >
            View tools
          </button>
          <small>
            Token env: AIRIS_MCP_TOKEN_{r.id.toUpperCase().replaceAll("-", "_")}
          </small>
        </div>
      ))}
      {selected && (
        <div>
          <h3>{selected.name}</h3>
          <select
            aria-label="MCP tool"
            value={tool}
            onChange={(e) => setTool(e.target.value)}
          >
            <option value="">Select tool</option>
            {tools.map((t) => (
              <option key={t.name}>{t.name}</option>
            ))}
          </select>
          <pre>
            {JSON.stringify(
              tools.find((t) => t.name === tool)?.inputSchema,
              null,
              2,
            )}
          </pre>
          <textarea
            aria-label="Tool arguments JSON"
            value={args}
            onChange={(e) => setArgs(e.target.value)}
          />
          <button
            disabled={!tool || busy}
            onClick={async () => {
              try {
                const arguments_ = JSON.parse(args);
                if (
                  !window.confirm(
                    "Confirm calling " +
                      selected.name +
                      " / " +
                      tool +
                      " with arguments:\n" +
                      args +
                      "\nThis may read or modify data in the connected service.",
                  )
                )
                  return;
                setBusy(true);
                const result = await api("/" + selected.id + "/call", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    name: tool,
                    arguments: arguments_,
                    confirmed: true,
                  }),
                });
                setNotice(JSON.stringify(result).slice(0, 16000));
              } catch (e: any) {
                setNotice(e.message);
              } finally {
                setBusy(false);
              }
            }}
          >
            Call tool (confirmation required)
          </button>
        </div>
      )}
      <pre role="status">{notice}</pre>
    </section>
  );
}
