# Installation Troubleshooting — Open Intelligence Lab

## Requirements

- Python 3.10 or higher (3.12 recommended)
- pip
- A terminal (PowerShell on Windows, Terminal on Mac/Linux)

---

## Windows — Common Issues

### ❌ `python` not recognized
**Cause:** Python isn't in your PATH, or only the broken Microsoft Store version is installed.

**Fix:**
1. Download the real Python installer from https://python.org/downloads
2. Run it — **check "Add Python to PATH"** before clicking Install
3. Open Start Menu → search "Manage app execution aliases"
4. Turn OFF `python.exe` and `python3.exe` (the Store versions)
5. Close and reopen PowerShell, then run `python --version`

### ❌ `venv\Scripts\activate` — script execution disabled
**Cause:** PowerShell blocks unsigned scripts by default.

**Fix (run once):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Or use Command Prompt (cmd.exe) instead — activation works there without any policy change.

### ❌ `ModuleNotFoundError: No module named 'api'`
**Cause:** You're running uvicorn from the wrong folder, or PYTHONPATH isn't set.

**Fix — always run these two commands together:**
```powershell
cd C:\path\to\open-intelligence-lab
$env:PYTHONPATH = $PWD
uvicorn api.main:app --reload --port 8000
```

### ❌ `ModuleNotFoundError: No module named 'networkx'`
**Cause:** Dependencies aren't installed in the active Python environment.

**Fix:**
```powershell
python -m pip install -r requirements.txt
```

---

## All Platforms — Quick Start

```bash
# 1. Clone
git clone https://github.com/AlborzNazari/open-intelligence-lab.git
cd open-intelligence-lab

# 2. Create virtual environment
python -m venv venv

# 3. Activate
# Mac/Linux:
source venv/bin/activate
# Windows PowerShell:
venv\Scripts\activate
# Windows CMD:
venv\Scripts\activate.bat

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start API (Terminal 1)
# Mac/Linux:
uvicorn api.main:app --reload --port 8000
# Windows — must set PYTHONPATH first:
$env:PYTHONPATH = $PWD
uvicorn api.main:app --reload --port 8000

# 6. Open dashboard (Terminal 2)
python demo.py
```

---

## Verify it's working

```bash
# Should return node_count: 37
curl http://localhost:8000/intelligence/graph/summary

# Should return 22 threat entities + 15 attack patterns
curl "http://localhost:8000/intelligence/entities?limit=5"

# Full API docs
open http://localhost:8000/docs
```

---

## Still stuck?

Open an issue at https://github.com/AlborzNazari/open-intelligence-lab/issues
