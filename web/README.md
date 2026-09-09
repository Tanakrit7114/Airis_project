# JARVIS University Web UI

React + Vite frontend for the FastAPI backend.

```bash
npm install
npm run dev
```

For a single-process deployment, build it first:

```bash
npm run build
```

Then start `../scripts/run_web.sh` from the project root. FastAPI serves `web/dist` when present.

### Markdown / Math
Assistant messages are rendered as Markdown with GFM and KaTeX math. After updating the project, run `npm install` again in `web/` so the new rendering dependencies are installed.
