# Contributing to Open Intelligence Lab

Thank you for your interest in contributing.  
This project is an ethical, explainable OSINT research platform.  
All contributions must follow the principles of transparency, privacy protection, and public-only intelligence sourcing.

---

## Getting Started — Local Setup

### Requirements
- Python 3.10 or higher (3.12 recommended)
- Git 2.x

### Step 1 — Clone the repository

```bash
git clone https://github.com/AlborzNazari/open-intelligence-lab.git
cd open-intelligence-lab
```

### Step 2 — Create and activate a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If you see a script execution error, run this first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

> **Important:** Only install from the root `requirements.txt`.  
> Do not run `pip install -r backend/requirements.txt` — that file pins older versions for reference only and will conflict on Python 3.12+.

### Step 4 — Run the API server

```bash
python -m uvicorn api.main:app --reload --port 8000
```

Then open `http://localhost:8000/docs` in your browser.

---

## Fixing Python PATH Confusion on Windows

Windows sometimes installs multiple Python versions — one from python.org and one from the Microsoft Store. When this happens, `pip install` may install packages into the wrong Python, and commands like `uvicorn` or `python` resolve to the wrong interpreter.

**How to check which Python your terminal is using:**
```powershell
where.exe python
python --version
```

If you see a path like `C:\Users\...\AppData\Local\Microsoft\WindowsApps\python.exe`, that is the Microsoft Store alias — not a real installation. It does not share packages with your project venv.

**Fix — always use `python -m` prefix inside the venv:**
```powershell
# Instead of: uvicorn ...
python -m uvicorn api.main:app --reload --port 8000

# Instead of: pip install ...
python -m pip install -r requirements.txt
```

**Fix — point to the correct Python when creating the venv:**

If `python` resolves to the wrong version, find your real Python path and use it explicitly:
```powershell
# Find all Python installations
where.exe python

# Use the full path to create the venv
C:\Users\YourName\AppData\Local\Programs\Python\Python312\python.exe -m venv venv
.\venv\Scripts\Activate.ps1
python --version   # should now show Python 3.12.x inside the venv
```

**Fix — disable the Microsoft Store Python aliases:**

Open Windows Settings → Apps → Advanced app settings → App execution aliases, then toggle off both `python.exe` and `python3.exe` aliases. After this, the `python` command will correctly resolve to your installed Python.

---

## Repository Conventions

### Line Endings (CRLF / LF)
We use a `.gitattributes` file in the root to enforce consistent line endings across Windows, macOS, and Linux.

---

## Contribution Guidelines

### 1. Ethical Requirements
- Only public, non-sensitive OSINT data is allowed.
- No scraping of restricted or private sources.
- No personal data or surveillance-oriented features.

### 2. How to Contribute
1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add or update documentation
5. Submit a pull request with a clear description

### 3. Areas You Can Contribute To
- Knowledge graph logic
- Risk scoring models
- Explanation engine
- Visualization tools
- Public OSINT datasets
- MISP / TAXII feed connectors
- Provenance and trust scoring
- Documentation and research notes

---

## Code Style
- Keep modules small and focused
- Use clear naming conventions
- Add docstrings where needed
- Avoid unnecessary complexity

---

## Reporting Issues
Open an issue with:
- A clear description
- Steps to reproduce (if applicable)
- Proposed solutions (optional)

Thank you for helping build an open, ethical intelligence research platform.

Contact: leftmountains@gmail.com
