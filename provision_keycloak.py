"""Временный скрипт: провижининг Keycloak + проверка авторизации через реальный JWT."""
import json

import httpx

BASE = "http://localhost:8080"
REALM = "watch"


def admin_token() -> str:
    r = httpx.post(
        f"{BASE}/realms/master/protocol/openid-connect/token",
        data={"grant_type": "password", "client_id": "admin-cli", "username": "admin", "password": "admin"},
        timeout=20,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def provision() -> None:
    tok = admin_token()
    H = {"Authorization": f"Bearer {tok}"}

    # Realm watch
    r = httpx.post(f"{BASE}/admin/realms", json={"realm": REALM, "enabled": True}, headers=H, timeout=20)
    if r.status_code not in (201, 409):
        r.raise_for_status()

    # Клиент watch-backend (public)
    r = httpx.get(f"{BASE}/admin/realms/{REALM}/clients?clientId=watch-backend", headers=H)
    clients = r.json()
    if clients:
        client_id = clients[0]["id"]
    else:
        r = httpx.post(
            f"{BASE}/admin/realms/{REALM}/clients",
            json={
                "clientId": "watch-backend",
                "publicClient": True,
                "directAccessGrantsEnabled": True,
                "standardFlowEnabled": True,
                "redirectUris": ["*"],
            },
            headers=H,
        )
        r.raise_for_status()
        client_id = httpx.get(
            f"{BASE}/admin/realms/{REALM}/clients?clientId=watch-backend", headers=H
        ).json()[0]["id"]

    # Mapper групп в access token
    mappers = httpx.get(
        f"{BASE}/admin/realms/{REALM}/clients/{client_id}/protocol-mappers/models", headers=H
    ).json()
    if not any(m.get("name") == "groups" for m in mappers):
        httpx.post(
            f"{BASE}/admin/realms/{REALM}/clients/{client_id}/protocol-mappers/models",
            json={
                "name": "groups",
                "protocol": "openid-connect",
                "protocolMapper": "oidc-group-membership-mapper",
                "config": {
                    "claim.name": "groups",
                    "access.token.claim": "true",
                    "idtoken.claim": "true",
                    "userinfo.token.claim": "true",
                    "full.path": "false",
                },
            },
            headers=H,
        ).raise_for_status()

    # Группы
    group_ids = {}
    for g in ("personnel-managers", "project-managers", "occupancy-managers"):
        resp = httpx.get(f"{BASE}/admin/realms/{REALM}/groups?search={g}&exact=true", headers=H)
        existing = [x for x in resp.json() if x["name"] == g]
        if existing:
            group_ids[g] = existing[0]["id"]
        else:
            r = httpx.post(f"{BASE}/admin/realms/{REALM}/groups", json={"name": g}, headers=H)
            r.raise_for_status()
            group_ids[g] = httpx.get(
                f"{BASE}/admin/realms/{REALM}/groups?search={g}&exact=true", headers=H
            ).json()[0]["id"]

    # Пользователь manager1 + группы
    users = httpx.get(f"{BASE}/admin/realms/{REALM}/users?username=manager1&exact=true", headers=H).json()
    if users:
        uid = users[0]["id"]
    else:
        r = httpx.post(
            f"{BASE}/admin/realms/{REALM}/users",
            json={
                "username": "manager1",
                "email": "manager1@company.ru",
                "firstName": "Менеджер",
                "lastName": "Тестовый",
                "enabled": True,
                "credentials": [{"type": "password", "value": "secret", "temporary": False}],
            },
            headers=H,
        )
        r.raise_for_status()
        uid = httpx.get(
            f"{BASE}/admin/realms/{REALM}/users?username=manager1&exact=true", headers=H
        ).json()[0]["id"]

    for g in ("personnel-managers", "occupancy-managers"):
        member = httpx.get(
            f"{BASE}/admin/realms/{REALM}/users/{uid}/groups", headers=H
        ).json()
        if not any(x["id"] == group_ids[g] for x in member):
            httpx.put(
                f"{BASE}/admin/realms/{REALM}/users/{uid}/groups/{group_ids[g]}", headers=H
            ).raise_for_status()

    print("Keycloak provisioned: realm=watch, client=watch-backend, user=manager1/secret")


def get_user_token() -> str:
    r = httpx.post(
        f"{BASE}/realms/{REALM}/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "watch-backend",
            "username": "manager1",
            "password": "secret",
        },
        timeout=20,
    )
    r.raise_for_status()
    claims = r.json()
    payload = json.loads(
        __import__("base64").urlsafe_b64decode(claims["access_token"].split(".")[1] + "==")
    )
    print("Token claims: sub=%s groups=%s" % (payload.get("sub"), payload.get("groups")))
    return claims["access_token"]


if __name__ == "__main__":
    provision()
    get_user_token()
    print("PROVISION OK")