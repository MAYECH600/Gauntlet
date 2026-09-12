#!/usr/bin/env python3
import os
import time
import yaml
import requests

Wh = '\033[1;37m'
Gr = '\033[1;32m'
Cy = '\033[1;36m'
Re = '\033[1;31m'
Ye = '\033[1;33m'
reset = '\033[0m'

BANNER_ART = R"""
 $$$$$$\                             $$$$$$$$\ $$\            $$\     
$$  __$$\                            \__$$  __|$$ |           $$ |    
$$ /  \__| $$$$$$\  $$\   $$\ $$$$$$$\  $$ |   $$ | $$$$$$\ $$$$$$\   
$$ |$$$$\  \____$$\ $$ |  $$ |$$  __$$\ $$ |   $$ |$$  __$$\\_$$  _|  
$$ |\_$$ | $$$$$$$ |$$ |  $$ |$$ |  $$ |$$ |   $$ |$$$$$$$$ | $$ |    
$$ |  $$ |$$  __$$ |$$ |  $$ |$$ |  $$ |$$ |   $$ |$$   ____| $$ |$$\ 
\$$$$$$  |\$$$$$$$ |\$$$$$$  |$$ |  $$ |$$ |   $$ |\$$$$$$$\  \$$$$  |
 \______/  \_______| \______/ \__|  \__|\__|   \__| \_______|  \____/ 
"""

CONFIG_PATH = "config.yaml"
DEFAULT_CONFIG = {
    "base_url": "http://localhost:5000",
    "login_endpoint": "/api/login",
    "logout_endpoint": "/api/logout",
    "protected_endpoint": "/api/profile",
    "state_changing_endpoint": "/api/account/update",
    "test_user": {"email": "Admin@hotel.com", "password": "admin1234"},
}

# Results collected across a run, for the final checklist
results = []


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            cfg = yaml.safe_load(f) or {}
        merged = {**DEFAULT_CONFIG, **cfg}
        merged["test_user"] = {**DEFAULT_CONFIG["test_user"], **cfg.get("test_user", {})}
        return merged
    print(f"{Ye}No config.yaml found — using defaults ({DEFAULT_CONFIG['base_url']}).{reset}")
    return DEFAULT_CONFIG


config = load_config()


def record(check_name, passed, detail=""):
    results.append({"check": check_name, "passed": passed, "detail": detail})
    status = f"{Gr}PASS{reset}" if passed else f"{Re}FAIL{reset}"
    print(f"  [{status}] {detail}")


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    print(f"{Cy}{BANNER_ART}{reset}")
    print(f"{Wh}--------------------------------------------")
    print(f"{Gr} A python testing tool for session management and web application security testing")
    print(f"{Wh}   Target: {config['base_url']}")
    print(f"{Wh}--------------------------------------------{reset}")


def with_header(func):
    def wrapper(*args, **kwargs):
        clear()
        print(f"{Cy}== {func.__name__.replace('_', ' ').title()} =={reset}\n")
        return func(*args, **kwargs)
    return wrapper


def login(session):
    """Performs a login and returns the response. Caller inspects session.cookies."""
    url = config["base_url"] + config["login_endpoint"]
    return session.post(url, json=config["test_user"], timeout=10)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

@with_header
def cookie_flags():
    session = requests.Session()
    try:
        resp = login(session)
    except requests.RequestException as e:
        record("cookie_flags", False, f"Request failed: {e}")
        return

    if not session.cookies:
        record("cookie_flags", False, "No cookies set on login response.")
        return

    for cookie in session.cookies:
        raw = resp.headers.get("Set-Cookie", "")
        has_secure = cookie.secure
        has_httponly = "HttpOnly" in raw or bool(cookie._rest.get("HttpOnly"))
        has_samesite = cookie._rest.get("SameSite") is not None

        record(f"cookie_flags:{cookie.name}:Secure", has_secure,
               f"Secure flag on '{cookie.name}'")
        record(f"cookie_flags:{cookie.name}:HttpOnly", has_httponly,
               f"HttpOnly flag on '{cookie.name}'")
        record(f"cookie_flags:{cookie.name}:SameSite", has_samesite,
               f"SameSite flag on '{cookie.name}'")


@with_header
def csrf():
    session = requests.Session()
    try:
        login(session)
    except requests.RequestException as e:
        record("csrf", False, f"Login failed: {e}")
        return

    url = config["base_url"] + config["state_changing_endpoint"]
    try:
        # Deliberately send a state-changing request with NO CSRF token.
        resp = session.post(url, json={"probe": "csrf_test"}, timeout=10)
    except requests.RequestException as e:
        record("csrf", False, f"Request failed: {e}")
        return

    # A protected endpoint should reject this — 403/400/401 expected.
    blocked = resp.status_code in (400, 401, 403)
    record("csrf:no_token_rejected", blocked,
           f"State-changing request without CSRF token -> HTTP {resp.status_code}")


@with_header
def session_management():
    """Session fixation check: session ID must change after authentication."""
    session = requests.Session()

    # Hit the app pre-auth to capture whatever session cookie it issues first.
    try:
        session.get(config["base_url"], timeout=10)
    except requests.RequestException as e:
        record("session_fixation", False, f"Initial request failed: {e}")
        return

    pre_auth_cookies = {c.name: c.value for c in session.cookies}

    try:
        login(session)
    except requests.RequestException as e:
        record("session_fixation", False, f"Login failed: {e}")
        return

    post_auth_cookies = {c.name: c.value for c in session.cookies}

    if not pre_auth_cookies:
        record("session_fixation", True,
               "No pre-auth session cookie issued (nothing to fixate).")
        return

    changed = any(
        pre_auth_cookies.get(name) != post_auth_cookies.get(name)
        for name in pre_auth_cookies
    )
    record("session_fixation", changed,
           "Session ID changes after login" if changed
           else "Session ID unchanged after login — fixation risk")


@with_header
def token_expiry():
    session = requests.Session()
    try:
        resp = login(session)
    except requests.RequestException as e:
        record("token_expiry", False, f"Login failed: {e}")
        return

    token = None
    try:
        body = resp.json()
        token = body.get("token") or body.get("access_token")
    except ValueError:
        pass

    if not token:
        record("token_expiry", False,
               "No token found in login response body — check field name or adjust for cookie-based sessions.")
        return

    protected_url = config["base_url"] + config["protected_endpoint"]

    # Sanity check: token should currently work.
    ok_resp = requests.get(protected_url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    if ok_resp.status_code not in (200, 201):
        record("token_expiry:token_currently_valid", False,
               f"Fresh token rejected unexpectedly -> HTTP {ok_resp.status_code}")
        return

    print(f"  {Wh}Token acquired. This check only confirms current validity;{reset}")
    print(f"  {Wh}re-run after your token's expected TTL to confirm it's rejected then.{reset}")
    record("token_expiry:token_currently_valid", True, "Fresh token accepted by protected endpoint")


@with_header
def session_invalidation():
    session = requests.Session()
    try:
        login(session)
    except requests.RequestException as e:
        record("session_invalidation", False, f"Login failed: {e}")
        return

    protected_url = config["base_url"] + config["protected_endpoint"]
    logout_url = config["base_url"] + config["logout_endpoint"]

    pre_logout = session.get(protected_url, timeout=10)
    if pre_logout.status_code not in (200, 201):
        record("session_invalidation", False,
               f"Could not access protected endpoint while logged in -> HTTP {pre_logout.status_code}")
        return

    try:
        session.post(logout_url, timeout=10)
    except requests.RequestException as e:
        record("session_invalidation", False, f"Logout request failed: {e}")
        return

    # Reuse the exact same session/cookies after logout.
    post_logout = session.get(protected_url, timeout=10)
    invalidated = post_logout.status_code in (401, 403)
    record("session_invalidation", invalidated,
           f"Protected endpoint after logout -> HTTP {post_logout.status_code}")


@with_header
def run_all_and_report():
    results.clear()
    for fn in (cookie_flags, csrf, session_management, token_expiry, session_invalidation):
        fn.__wrapped__() if hasattr(fn, "__wrapped__") else fn()
        print()
    print_checklist()


def print_checklist():
    clear()
    print(f"{Cy}== Session Security Checklist =={reset}\n")
    for r in results:
        status = f"{Gr}PASS{reset}" if r["passed"] else f"{Re}FAIL{reset}"
        print(f"  [{status}] {r['detail']}")
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n{Wh}{passed}/{total} checks passed{reset}")


# ---------------------------------------------------------------------------
# Menu plumbing
# ---------------------------------------------------------------------------

def option_text(options):
    text = ""
    for opt in options:
        text += f"{Wh}[ {opt['num']} ] {Gr}{opt['text']}\n"
    return text


def is_in_options(options, num):
    return any(opt['num'] == num for opt in options)


def call_option(options, num):
    if not is_in_options(options, num):
        raise ValueError("Option not found")
    for opt in options:
        if opt['num'] == num:
            opt['func']()
            return


def execute_option(options, num):
    try:
        call_option(options, num)
        input(f"\n{Wh}[ {Gr}+ {Wh}] {Gr}Press enter to continue{reset}")
    except ValueError as e:
        print(f"{Re}{e}{reset}")
        time.sleep(1.5)
    except KeyboardInterrupt:
        print(f"\n{Wh}[ {Re}! {Wh}] {Re}Exit{reset}")
        time.sleep(1)
        raise SystemExit


def show_menu(options):
    clear()
    show_banner()
    print(f"\n{option_text(options)}")


def run_menu(options):
    while True:
        show_menu(options)
        try:
            choice = int(input(f"{Wh}\n [ + ] {Gr}Select option: {Wh}"))
        except ValueError:
            print(f"\n{Wh}[ {Re}! {Wh}] {Re}Please enter a number{reset}")
            time.sleep(1.5)
            continue
        execute_option(options, choice)


options = [
    {'num': 1, 'text': 'Cookie Flags Check', 'func': cookie_flags},
    {'num': 2, 'text': 'CSRF Check', 'func': csrf},
    {'num': 3, 'text': 'Session Fixation Check', 'func': session_management},
    {'num': 4, 'text': 'Token Expiry Check', 'func': token_expiry},
    {'num': 5, 'text': 'Session Invalidation Check', 'func': session_invalidation},
    {'num': 6, 'text': 'Run All + Checklist Report', 'func': run_all_and_report},
    {'num': 0, 'text': 'Exit', 'func': lambda: (_ for _ in ()).throw(SystemExit)},
]


if __name__ == '__main__':
    try:
        run_menu(options)
    except (KeyboardInterrupt, SystemExit):
        print(f"\n{Wh}[ {Re}! {Wh}] {Re}Exit{reset}")
        time.sleep(1)