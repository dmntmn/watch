"""Временная проверка OIDC Authorization Code + PKCE для клиента watch-frontend.

Имитирует SPA: authorize -> логин -> code -> token exchange -> вызов API.
"""
import base64
import hashlib
import os
import re
import sys

import httpx

BASE = "http://localhost:8080"
REDIRECT = "http://localhost:5173/"

# PKCE
verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode()
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()

params = {
    "client_id": "watch-frontend",
    "response_type": "code",
    "scope": "openid",
    "redirect_uri": REDIRECT,
    "code_challenge": challenge,
    "code_challenge_method": "S256",
    "state": "test-state",
}

with httpx.Client(follow_redirects=False, timeout=20) as c:
    r = c.get(f"{BASE}/realms/watch/protocol/openid-connect/auth", params=params)
    print("[1] authorize ->", r.status_code, r.headers.get("location", "-")[:80])

    html = r.text
    action = re.search(r'<form[^>]+action="([^"]+)"', html)
    if not action:
        print("LOGIN FORM NOT FOUND")
        sys.exit(1)
    login_url = action.group(1).replace("&", "&")
    print("[2] login form url:", login_url[:90])

    # Все скрытые поля формы (Keycloak 26 требует credentialId и пр.)
    form_data = {"username": "manager1", "password": "secret"}
    for name, value in re.findall(
        r'<input[^>]+type="hidden"[^>]+name="([^"]+)"[^>]+value="([^"]*)"', html
    ):
        form_data[name] = value.replace("&", "&")
    for name, value in re.findall(
        r'<input[^>]+name="([^"]+)"[^>]+type="hidden"[^>]+value="([^"]*)"', html
    ):
        form_data[name] = value.replace("&", "&")

    print("[2b] hidden fields:", sorted(form_data.keys()))
    r2 = c.post(login_url, data=form_data, headers={"Referer": str(r.url)})
    print("[3] login ->", r2.status_code, r2.headers.get("location", "-")[:90])
    if r2.status_code != 302:
        print("[3b] body snippet:", re.sub(r"<[^>]+>", " ", r2.text)[:200])
    if r2.status_code == 302:
        loc = r2.headers["location"]
    elif r2.text and "error" in r2.text.lower():
        print("LOGIN FAILED")
        sys.exit(1)
    else:
        # иногда отдаёт HTML с редиректом
        loc = r2.headers.get("location", "")

    # переход по редиректу до получения code
    final = None
    for _ in range(6):
        r3 = c.get(loc) if loc.startswith("http") else c.post(f"{BASE}{loc}" if loc.startswith("/") else loc)
        loc2 = r3.headers.get("location")
        if r3.status_code == 302 and loc2:
            loc = loc2
        else:
            final = r3
            break
    url = str(final.url)
    m = re.search(r"[?&]code=([^&]+)", url)
    print("[4] code obtained:", bool(m), "| state:", re.search(r"[?&]state=([^&]+)", url).group(1) if re.search(r"[?&]state=([^&]+)", url) else "-")
    if not m:
        sys.exit(1)

    # Обмен кода на токен
    tok = c.post(
        f"{BASE}/realms/watch/protocol/openid-connect/token",
        data={
            "grant_type": "authorization_code",
            "client_id": "watch-frontend",
            "code": m.group(1),
            "redirect_uri": REDIRECT,
            "code_verifier": verifier,
        },
    )
    print("[5] token exchange ->", tok.status_code)
    token = tok.json()["access_token"]

    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    import json
    claims = json.loads(base64.urlsafe_b64decode(payload))
    print("[6] claims: groups =", claims.get("groups"), "| azp =", claims.get("azp"))

    # Вызов backend API с токеном
    me = c.get(
        "http://127.0.0.1:8000/api/v1/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    print("[7] GET /api/v1/me ->", me.status_code, me.json().get("email") if me.status_code == 200 else me.text[:120])

    view = c.get(
        "http://127.0.0.1:8000/api/v1/view/init",
        params={"from": "2026-09-01T00:00:00", "to": "2026-10-01T00:00:00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    print("[8] GET /view/init ->", view.status_code, "periods:", len(view.json().get("periods", [])) if view.status_code == 200 else view.text[:120])

print("OIDC FLOW OK")