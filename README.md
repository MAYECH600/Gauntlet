# Session Security Test Suite

An automated pytest-based test suite that scans a running web application for common session-handling vulnerabilities — missing cookie flags, session fixation, CSRF gaps, and improper token expiry — and outputs a pass/fail security checklist.

## Overview

Session management bugs are among the most common — and most overlooked — web app vulnerabilities. This tool automates the manual checks a pentester would normally run by hand, giving developers a fast, repeatable way to catch session-handling issues before they ship.

## What it checks

| Check | Description |
|---|---|
| **Cookie flags** | Verifies `Secure`, `HttpOnly`, and `SameSite` attributes are set on session cookies |
| **Session fixation** | Confirms the session ID changes after login (not reused from a pre-auth session) |
| **CSRF protection** | Checks for CSRF tokens on state-changing requests and validates they're enforced server-side |
| **Token expiry** | Confirms session/auth tokens expire as expected and expired tokens are rejected |
| **Session invalidation** | Confirms sessions are properly invalidated on logout |

Each run produces a pass/fail checklist summarizing the results.

## Tech stack

- **pytest** — test runner and reporting
- **requests** — HTTP-level session and cookie inspection
- **Playwright** *(optional)* — for checks that require a real browser context (e.g. JS-driven cookie behavior)

## Installation

```bash
git clone https://github.com/MAYECH600/session-security-test-suite.git
cd session-security-test-suite
pip install -r requirements.txt
```

If using the Playwright-based checks:

```bash
playwright install
```

## Usage

Point the suite at a running instance of your app:

```bash
pytest --base-url http://localhost:5000
```

Run a specific check category:

```bash
pytest -k cookie_flags
pytest -k csrf
pytest -k session_fixation
pytest -k token_expiry
```

Generate a checklist report:

```bash
pytest --base-url http://localhost:5000 --html=report.html
```

## Configuration

Set target app details and test credentials in `config.yaml` (or via environment variables):

```yaml
base_url: http://localhost:5000
login_endpoint: /api/login
logout_endpoint: /api/logout
test_user:
  username: testuser
  password: testpass123
```

> **Note:** Only run this suite against applications you own or have explicit authorization to test.

## Project structure

```
session-security-test-suite/
├── tests/
│   ├── test_cookie_flags.py
│   ├── test_session_fixation.py
│   ├── test_csrf.py
│   └── test_token_expiry.py
├── config.yaml
├── requirements.txt
└── README.md
```

## Roadmap

- [ ] Add JWT-specific checks (algorithm confusion, weak signing secrets)
- [ ] Add concurrent-session / session-limit checks
- [ ] CI integration example (GitHub Actions)

## License

MIT