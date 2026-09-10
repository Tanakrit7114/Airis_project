import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import hljs from "highlight.js/lib/common";
import "highlight.js/styles/github-dark.css";
import "../artifacts.css";

const CODE_EXTENSIONS: Record<string, string> = {
  javascript: "js", js: "js", jsx: "jsx", typescript: "ts", ts: "ts", tsx: "tsx",
  python: "py", py: "py", css: "css", json: "json", sql: "sql", yaml: "yaml", yml: "yml",
  markdown: "md", md: "md", xml: "xml", svg: "svg", bash: "sh", shell: "sh", sh: "sh",
  java: "java", c: "c", cpp: "cpp", csharp: "cs", cs: "cs", go: "go", rust: "rs",
  ruby: "rb", php: "php", swift: "swift", kotlin: "kt", text: "txt", plaintext: "txt",
};

export default function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noreferrer">
              {children}
            </a>
          ),
          pre: ({ children }) => {
            const child = React.Children.toArray(children)[0];
            if (React.isValidElement(child)) {
              const props = child.props as {
                className?: string;
                children?: React.ReactNode;
              };
              return (
                <CodeBlock
                  className={props.className}
                  code={String(props.children ?? "").replace(/\n$/, "")}
                />
              );
            }
            return <pre>{children}</pre>;
          },
          code: ({ children, className }) => (
            <code className={className || "inline-code"}>{children}</code>
          ),
          table: ({ children }) => (
            <div className="table-scroll">
              <table>{children}</table>
            </div>
          ),
        }}
      >
        {content || ""}
      </ReactMarkdown>
    </div>
  );
}
function CodeBlock({ className, code }: { className?: string; code: string }) {
  const [notice, setNotice] = useState(""),
    [preview, setPreview] = useState<string | null>(null);
  const lang = className?.match(/(?:^|\s)language-([^\s]+)/)?.[1].toLowerCase() || "text";
  const isHtml =
    /^(html|htm)$/i.test(lang) || /^\s*(<!doctype html|<html[\s>])/i.test(code);
  const highlighted = hljs.getLanguage(lang)
    ? hljs.highlight(code, { language: lang }).value
    : null;
  const copy = async () => {
    try {
      if (navigator.clipboard && window.isSecureContext)
        await navigator.clipboard.writeText(code);
      else {
        const field = document.createElement("textarea");
        field.value = code;
        field.style.position = "fixed";
        field.style.opacity = "0";
        document.body.append(field);
        try {
          field.select();
          if (!document.execCommand("copy")) throw Error();
        } finally {
          field.remove();
        }
      }
      setNotice("Copied");
    } catch {
      setNotice("Could not copy. Select the code and press Ctrl/Cmd+C.");
    }
  };
  const download = () => {
    try {
      const url = URL.createObjectURL(
        new Blob([code], {
          type: isHtml ? "text/html;charset=utf-8" : "text/plain;charset=utf-8",
        }),
      );
      const a = document.createElement("a");
      a.href = url;
      a.download = isHtml ? "airis-website.html" : `airis-code.${CODE_EXTENSIONS[lang] || "txt"}`;
      a.hidden = true;
      document.body.append(a);
      try {
        a.click();
        setNotice("Download started");
      } finally {
        a.remove();
        // Leave the Blob alive while browsers and Electron start the download.
        setTimeout(() => URL.revokeObjectURL(url), 60_000);
      }
    } catch {
      setNotice("Could not download. Copy the code to save it locally.");
    }
  };
  const show = () => {
    const doc = new DOMParser().parseFromString(code, "text/html");
    // Redirects are not useful in an inline preview and would replace it with
    // an external page. Download preserves the original source unchanged.
    doc.querySelectorAll('meta[http-equiv="refresh" i], base').forEach((node) => node.remove());
    const policy = doc.createElement("meta");
    policy.httpEquiv = "Content-Security-Policy";
    policy.content =
      "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; form-action 'none'; frame-src 'none'; base-uri 'none'";
    doc.head.prepend(policy);
    setPreview("<!doctype html>" + doc.documentElement.outerHTML);
  };
  return (
    <div className="code-shell">
      <div className="airis-code-toolbar">
        <span>{lang}</span>
        <button onClick={copy}>Copy code</button>
        <button onClick={download}>
          {isHtml ? "Download HTML" : "Download code"}
        </button>
        {isHtml && <button onClick={show}>Open / refresh preview</button>}
        <span role="status">{notice}</span>
      </div>
      <pre className="code-block">
        {highlighted ? (
          <code dangerouslySetInnerHTML={{ __html: highlighted }} />
        ) : (
          <code>{code}</code>
        )}
      </pre>
      {preview !== null && (
        <section className="airis-preview">
          <button onClick={() => setPreview(null)}>Close preview</button>
          <iframe
            title="HTML website preview"
            sandbox="allow-scripts"
            referrerPolicy="no-referrer"
            srcDoc={preview}
          />
        </section>
      )}
    </div>
  );
}
