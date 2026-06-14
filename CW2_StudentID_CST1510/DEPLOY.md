# Deploying HelpHub

> **Why not Vercel?** Vercel runs short-lived *serverless* functions and can't
> host a Streamlit app — Streamlit needs a long-running server holding an open
> WebSocket to the browser, plus a writable disk for the SQLite database.
> **Streamlit Community Cloud** is free and purpose-built for this, so that's
> what this guide uses.

The end result is a public link like
`https://helphub-yourname.streamlit.app` that you can open in your demo video.

---

## Step 1 — Put the project on GitHub

You need [Git](https://git-scm.com/downloads) installed and a free
[GitHub account](https://github.com/signup).

### 1a. Create an empty repo on GitHub
1. Go to <https://github.com/new>
2. Repository name: `helphub-cst1510` (or anything)
3. Set it to **Public** (Streamlit Community Cloud needs to read it; private
   also works but public is simplest for a coursework demo)
4. **Do NOT** tick "Add a README" — the project already has one
5. Click **Create repository**. Leave the page open — you'll need the URL it
   shows (looks like `https://github.com/YOURNAME/helphub-cst1510.git`)

### 1b. Push the code from your computer
Open a terminal **inside the `CW2_StudentID_CST1510` folder** and run:

```bash
git init
git add .
git commit -m "HelpHub customer service platform"
git branch -M main
git remote add origin https://github.com/YOURNAME/helphub-cst1510.git
git push -u origin main
```

Replace `YOURNAME/helphub-cst1510` with your actual repo URL. If Git asks you to
sign in, use your GitHub username and a
[Personal Access Token](https://github.com/settings/tokens) as the password
(GitHub no longer accepts your account password on the command line).

> The included `.gitignore` keeps the local database and any API key out of the
> repo automatically — only the source code and the CSV seed data are pushed.

---

## Step 2 — Deploy on Streamlit Community Cloud

1. Go to <https://share.streamlit.io> and click **Sign in with GitHub**, then
   authorise it.
2. Click **Create app → Deploy a public app from GitHub**.
3. Fill in:
   - **Repository:** `YOURNAME/helphub-cst1510`
   - **Branch:** `main`
   - **Main file path:** `main.py`
   - **App URL:** pick something like `helphub-yourname`
4. Click **Deploy**. First build takes ~2-3 minutes while it installs
   `requirements.txt`. When it's done you'll have your public URL. 🎉

The database is created and seeded automatically on first load, so the
dashboard, inbox and charts are populated immediately. Log in with
`admin` / `admin123`.

---

## Step 3 (optional) — Enable the OpenAI AI assistant

The Copilot works in **offline mode** with no key. To switch it to the live
OpenAI API on the deployed app:

1. In Streamlit Cloud, open your app → **⋮ menu → Settings → Secrets**.
2. Paste:
   ```toml
   OPENAI_API_KEY = "sk-your-key-here"
   ```
   (Optionally add `OPENAI_BASE_URL` and `OPENAI_MODEL` for a free/compatible
   provider — see Video 09.)
3. Save. The app restarts and the sidebar will show **🟢 AI: OpenAI connected**.

Secrets are private and are **not** stored in your GitHub repo.

---

## Updating the live app later

Any time you change the code:

```bash
git add .
git commit -m "describe your change"
git push
```

Streamlit Cloud auto-redeploys within a few seconds of the push.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Build fails on a package | Check `requirements.txt` is in the repo root and spelled correctly. |
| "Main file not found" | The main file path must be exactly `main.py`. |
| App loads but no data | The DB seeds on startup; click **⋮ → Reboot** once. |
| AI shows offline mode | Add `OPENAI_API_KEY` in Settings → Secrets (Step 3). |
| `git push` rejected | Use a Personal Access Token as your password, not your GitHub password. |

---

## Alternative free hosts (all run Streamlit properly)

- **Hugging Face Spaces** — create a Space, choose the **Streamlit** SDK, push
  the same files. Public URL, no card required.
- **Render** — New → Web Service → Build `pip install -r requirements.txt`,
  Start `streamlit run main.py --server.port $PORT --server.address 0.0.0.0`.
- **Railway** — similar to Render with the same start command.
