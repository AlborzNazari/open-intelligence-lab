# Troubleshooting — Open Intelligence Lab

## Requirements

- Python 3.10 or higher (3.12 recommended)
- pip
- A terminal (PowerShell on Windows, Terminal on Mac/Linux)
- Docker Desktop 25+ (for Docker option only)

---

## The Golden Rules

Before anything else:

1. **Always run commands from the project root** — `C:\Users\yourname\open-intelligence-lab` — never from inside `api/` or any subfolder
2. **Always use `python -m uvicorn`** — never bare `uvicorn` on Windows (it resolves to the wrong Python)
3. **Never run uvicorn and Docker at the same time** — they both want port 8000 and will conflict
4. **Open `index.html` as a local file** — double-click it in File Explorer, do not type a file path in the browser

---

## Windows — Common Issues

### ❌ `ModuleNotFoundError: No module named 'networkx'` (or any other module)

**Cause:** You have two Python installations — the Microsoft Store version and the real one. `pip install` went to one, `python` runs the other.

**Fix — always use `python -m pip`, never bare `pip`:**
```powershell
python -m pip install -r requirements.txt
```

**Permanent fix — disable the Store aliases:**
1. Start Menu → search "Manage app execution aliases"
2. Turn OFF `python.exe` and `python3.exe`
3. Reopen PowerShell and reinstall

---

### ❌ `ModuleNotFoundError: No module named 'api'`

**Cause:** You ran uvicorn from inside the `api/` folder instead of the project root.

**Fix:**
```powershell
cd C:\Users\albor\open-intelligence-lab   # project root
python -m uvicorn api.main:app --reload --port 8000
```

---

### ❌ `uvicorn` is not recognized

**Cause:** Bare `uvicorn` command doesn't resolve correctly on Windows when multiple Python versions are installed.

**Fix — always use the module form:**
```powershell
python -m uvicorn api.main:app --reload --port 8000
```

---

### ❌ `venv\Scripts\activate` — script execution disabled

**Cause:** PowerShell blocks unsigned scripts by default.

**Fix (run once):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### ❌ `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Cause:** Either a previous uvicorn process is still running, or Docker is using port 8000.

**Fix — find and kill what's on 8000:**
```powershell
netstat -ano | findstr :8000
```
Take the PID from the last column:
```powershell
taskkill /PID <pid-number> /F
```

Or kill all Python processes at once:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
```

**Important:** Never run uvicorn manually while `docker compose up` is running. Pick one or the other.

---

## Browser — Mixed Content Block

### ❌ Graph doesn't load from `https://alborznazari.github.io/open-intelligence-lab/`

**Cause:** GitHub Pages serves over HTTPS. Your local API runs over HTTP. Browsers block HTTPS pages from calling HTTP endpoints — this is called a mixed content block.

**You will see in the browser console:**
```
Access to fetch at 'http://localhost:8000/...' has been blocked by CORS policy
```

**Fix A — Open `index.html` as a local file (recommended for development):**

Double-click `index.html` in File Explorer. It opens as `file://` which is allowed to call `http://localhost:8000` freely. No mixed content, no errors.

**Fix B — Firefox (for testing the GitHub Pages version):**

1. Open Firefox
2. Go to `about:config`
3. Search `security.mixed_content.block_active_content`
4. Click the toggle → set to `false`
5. Open the GitHub Pages URL

**Fix C — Chrome (allow mixed content for this site):**

1. Open `https://alborznazari.github.io/open-intelligence-lab/`
2. Click the lock icon in the address bar → **Site settings**
3. Find **Insecure content** → set to **Allow**
4. Refresh

**Fix D — Docker + Caddy (permanent HTTPS proxy):**

See the Docker section below. `docker compose up` starts a Caddy container that wraps the API in HTTPS at `https://localhost:8443`. The GitHub Pages frontend auto-detects HTTPS and switches to this endpoint — no browser config needed.

---

## Docker — Common Issues

### ❌ `Unknown server host 'db'`

**Cause:** The MISP container started before the database was ready, or the containers are not on the same Docker network.

**Fix — full clean restart:**
```powershell
docker compose down --volumes --remove-orphans
docker compose up
```

The `docker-compose.yml` uses `depends_on` with health checks so `misp` waits for `db` and `redis` to be healthy before starting.

---

### ❌ Container has empty `"Networks": {}`

**Cause:** Docker Desktop on Windows sometimes fails to attach containers to the compose network when leftover state from previous runs exists.

**Fix:**
```powershell
docker compose down --volumes --remove-orphans
docker network prune -f
docker compose up
```

---

### ❌ `failed to connect to the docker API` / Docker not running

**Cause:** Docker Desktop crashed or hasn't fully started.

**Fix:**
1. Find the Docker whale icon in the system tray (bottom right)
2. Right-click → Quit Docker Desktop
3. Open Docker Desktop from the Start menu
4. Wait until the whale icon stops animating (30–60 seconds)
5. Run your command again

---

### ❌ Caddy returns 502 Bad Gateway

**Cause:** Caddy started before the OI Lab API container was ready, or the containers aren't resolving each other by name.

**Fix:**
```powershell
docker restart oilab-caddy
```

If that doesn't help:
```powershell
docker compose down --volumes --remove-orphans
docker compose up
```

---

### ❌ `ERR AUTH <password> called without any password configured`

**Cause:** MISP tries to authenticate to Redis with a password but the local Redis has none set. This is a warning during initialization, not a fatal error — MISP continues starting up.

**This is expected behavior** in a local development setup. It does not prevent MISP from working.

---

### ❌ MISP takes too long / health check failing

**Cause:** MISP initializes a full database, runs migrations, updates threat lists, and configures itself on first boot. This takes 2–5 minutes.

**Fix:** Wait. Do not restart the containers during initialization. Watch the logs:
```powershell
docker logs oilab-misp --follow
```
When you see `MISP | Resolve non-critical issues` and then it goes quiet, MISP is ready.

---

### ❌ You ran `docker compose down` in the wrong folder

**Always check your prompt** before running Docker commands. The compose file must be in the current directory.

```powershell
cd C:\Users\albor\open-intelligence-lab
docker compose down
```

---

## MISP — Common Issues

### ❌ MISP Live Feed shows "inactive"

**Cause:** `MISP_URL` and `MISP_KEY` environment variables are not set.

**Fix — create a `.env` file in the project root:**
```
MISP_URL=https://localhost
MISP_KEY=your-api-key-from-misp-profile
```

Get your API key:
1. Open `https://localhost` in your browser
2. Login: `admin@admin.test` / `admin`
3. Top right → your username → **My Profile**
4. Scroll to **Auth key** → copy it

Then restart:
```powershell
docker compose down
docker compose up
```

---

### ❌ `MISP API error 403 — Authentication failed`

**Cause:** The API key is wrong, a placeholder, or the MISP instance hasn't finished initializing yet.

**Fix:**
- Make sure you copied the key from **My Profile → Auth key** in the MISP UI
- Make sure MISP has fully initialized before copying the key (wait for the quiet after startup)
- Make sure there are no extra spaces in the `.env` file

---

## Verify Everything Is Working

**API health check:**
```
http://127.0.0.1:8000/
```
Expected: `{"status":"ok","version":"0.4.0",...}`

**API docs:**
```
http://127.0.0.1:8000/docs
```

**Graph data:**
```
http://127.0.0.1:8000/intelligence/graph/summary
```
Expected: `{"node_count":37,...}`

**HTTPS proxy (Docker only):**
```
https://localhost:8443/
```
Accept the self-signed cert warning once. Expected: same JSON as above.

---

## Still stuck?

Open an issue at https://github.com/AlborzNazari/open-intelligence-lab/issues
