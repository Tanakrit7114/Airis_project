# Google OAuth on localhost

Use exactly this redirect URI in Google Cloud:

`http://localhost:8000/api/extensions/oauth/google/callback`

Set in `.env`:

`JARVIS_PUBLIC_BASE_URL=http://localhost:8000`

Use the same hostname in the browser: `http://localhost:8000`.
Do not mix `127.0.0.1` and `localhost`.
