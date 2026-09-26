# Watch Frontend — React + TypeScript

Клиент backend-сервиса учёта занятости работников.

## Стек

- Vite 6 + React 18 + TypeScript (strict)
- Ant Design v5 (тема через токены), react-router-dom, @tanstack/react-query
- keycloak-js: OIDC **Authorization Code + PKCE**
- axios (автоподстановка `Authorization: Bearer <token>`, retry при 401)
- socket.io-client (live-обновления)

## Запуск

```bash
cd frontend
npm install

# настройки (при необходимости)
cp .env.example .env.local

npm run dev      # http://localhost:5173
npm run build    # tsc -b && vite build (сборка в dist/)
npm run preview  # предпросмотр production-сборки
```

Требуется работающий backend (`uvicorn src.main:socket_app`) и Keycloak.
Провижининг Keycloak (realm, клиенты `watch-backend`/`watch-frontend`,
группы, тестовый пользователь):

```bash
.venv/bin/python scripts/provision_keycloak.py   # из корня проекта
```

Тестовый вход: `manager1` / `secret`.

## Переменные окружения

| Переменная | По умолчанию |
|---|---|
| VITE_API_URL | http://localhost:8000 |
| VITE_KEYCLOAK_URL | http://localhost:8080 |
| VITE_KEYCLOAK_REALM | watch |
| VITE_KEYCLOAK_CLIENT_ID | watch-frontend |

## Роли и видимость

| Группа Keycloak | Возможности в интерфейсе |
|---|---|
| personnel-managers | CRUD сотрудников и их записей |
| project-managers | CRUD проектов, месторождений, назначения |
| occupancy-managers | CRUD периодов занятости и финансов |
| admin | всё выше + страница «Аудит» |
| все аутентифицированные | чтение списков |

Скрытие действий — хук `usePermission()` и компонент `PermissionGate`
([`src/permissions.ts`](src/permissions.ts)).

## Страницы

- `/occupancy` — окно просмотра (по умолчанию текущий месяц), периоды всех
  8 видов с динамическими формами деталей, финансы с файлами; live-обновления
  через Socket.IO (`view:init` → `data:changed`)
- `/employees` — таблица сотрудников, суб-записи (образование, сертификаты,
  медосмотры, СИЗ) вкладками
- `/projects` — проекты, месторождения (expandable), назначение сотрудников
- `/audit` — аудит-лог (admin)

## Прод (nginx SPA)

Статику из `dist/` отдаёт nginx с `try_files $uri /index.html;`, запросы
`/api/*` и `/socket.io/*` проксируются на backend (пример — в корневом
[`nginx/nginx.conf`](../nginx/nginx.conf), секция SPA-сервера ниже):

```nginx
server {
    listen 80;
    root /var/www/watch-frontend/dist;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
    location /socket.io/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location / {
        try_files $uri /index.html;
    }
}