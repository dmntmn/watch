# Watch — сервис учёта занятости работников

Boilerplate программного комплекса:

- **PostgreSQL** (данные, UUID-ключи), SQLAlchemy 2.0 async + Alembic
- **REST API** (FastAPI): POST / GET / PUT / DELETE
- **Keycloak**: каждый запрос валидирует JWT (RS256/JWKS), профиль пользователя синхронизируется в БД сервиса
- **Live-обновления**: Socket.IO + Redis pub/sub — изменения доставляются всем слушателям (в т.ч. при нескольких инстансах за nginx)
- **Email-уведомления** работникам (SMTP) — работники не имеют доступа к системе
- **Файлы-подтверждения** доходов/расходов в S3 (MinIO локально)
- **Аудит**: любые изменения любой таблицы фиксируются с автором

## Быстрый старт

```bash
# 1. Инфраструктура (PostgreSQL, Redis, Keycloak)
docker compose up -d

#    MinIO (S3 для файлов) — опционально, если образ недоступен в вашем окружении:
#    docker compose --profile storage up -d minio
#    Можно использовать любой S3-совместимый сервис (см. S3_* в .env).

# 2. Окружение
cp .env.example .env

# 3. Миграции
alembic upgrade head

# 4. Запуск приложения
uvicorn src.main:socket_app --reload --port 8000
```

Сервисы:
| Сервис | Адрес |
|---|---|
| API + Socket.IO | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Keycloak | http://localhost:8080 (admin / admin) |
| MinIO консоль | http://localhost:9001 (minioadmin / minioadmin), запускается с `--profile storage` |

## Настройка Keycloak (realm)

Рекомендуемый путь — автоматический провижининг:

```bash
.venv/bin/python scripts/provision_keycloak.py
```

Скрипт создаёт realm `watch`, клиент `watch-backend` (public), мапперы групп
(`groups`) и audience (`aud=watch-backend`), группы
`personnel-managers` / `project-managers` / `occupancy-managers`,
тестового пользователя `manager1` / `secret` с группами персонала и занятости.

Либо вручную:

1. Создайте realm, например `watch`.
2. Создайте клиент `watch-backend` (Access Type: **public**, Valid redirect URIs под ваш фронтенд).
3. В клиенте добавьте mapper **Group Membership**:
   - Token Claim Name: `groups`
   - Add to access token: **ON**
4. (Рекомендуется) Добавьте mapper **Audience** с `included.client.audience = watch-backend`,
   чтобы `aud` токена содержал id клиента. Приложение принимает и стандартный
   вариант `aud=account` (проверяется `azp`/issuer).
5. Создайте группы (и назначьте пользователей):
   - `personnel-managers` — CRUD сотрудников
   - `project-managers` — CRUD проектов/месторождений, назначение сотрудников на проекты
   - `occupancy-managers` — периоды занятости и финансовые записи
   - Все аутентифицированные пользователи имеют доступ на чтение
6. (Опционально, ABAC-lite) Для ограничения видимости проектами добавьте
   mapper **Hardcoded claim** `projects` = JSON-массив UUID проектов, либо
   User Attribute `projects` с маппингом в access token. Если claim отсутствует — видна вся база.

Проверка токена: `KEYCLOAK_ISSUER`/`KEYCLOAK_JWKS_URL` по умолчанию выводятся из
`KEYCLOAK_SERVER_URL` + `KEYCLOAK_REALM`.

## REST API (префикс /api/v1)

| Метод | Путь | Права |
|---|---|---|
| POST/GET | `/employees`; GET/PUT/DELETE `/employees/{id}` | персонал (CRUD), чтение всем |
| POST/GET | `/employees/{id}/educations` (и `certifications`, `medical-exams`, `ppe-records`) | персонал |
| POST/GET | `/projects`; GET/PUT/DELETE `/projects/{id}` | проектный менеджер |
| POST/GET | `/projects/{id}/fields`; PUT/DELETE `/fields/{id}` | проектный менеджер |
| GET/POST | `/projects/{id}/employees` (назначение/снятие работника) | проектный менеджер |
| POST/GET | `/employment-periods`; GET/PUT/DELETE `/employment-periods/{id}` | группа занятости |
| GET/PUT/DELETE | `/employment-periods/{id}/{period_type}` (детали модуля) | группа занятости |
| GET/POST | `/employment-periods/{id}/financial-records`; PUT/DELETE `/financial-records/{id}` | группа занятости |
| POST | `/financial-records/{id}/attachments`; GET `/attachments/{id}` | загрузка — группа занятости, скачивание — чтение |
| GET | `/view/init?from=&to=` — snapshot за окно просмотра (по умолчанию текущий месяц) | чтение |
| GET | `/audit-logs?entity=&entity_id=` | чтение |
| GET | `/me` | любой аутентифицированный |

Виды занятости (`period_type`): `shift` (вахта), `vacation` (отпуск),
`sick_leave` (больничный), `flight` (перелёт), `hotel` (гостиница),
`train` (поезд), `taxi` (такси), `other` (другое).

Пример создания периода с деталями вахты:

```bash
curl -X POST http://localhost:8000/api/v1/employment-periods \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "<uuid>",
    "period_type": "shift",
    "started_at": "2026-10-01T08:00:00+05:00",
    "ended_at": "2026-10-15T18:00:00+05:00",
    "details": {"field_id": "<uuid месторождения>", "notes": "Вахта 15/15"}
  }'
```

## Socket.IO протокол

Подключение передаёт токен в `auth`: `io("http://host", {auth: {token}})`.

| Событие (клиент → сервер) | Данные | Ответ |
|---|---|---|
| `view:init` | `{from?, to?, project_ids?}` | `view:snapshot` (полный snapshot окна) |
| `view:close` | — | `view:closed` |

При любом изменении данных сервер шлёт `data:changed`:
`{entity, action, payload, period_start, period_end, project_ids}` — клиент
обновляет экран без перезагрузки.

### Доставка через Redis pub/sub

1. Сервис после `commit` публикует доменное событие в канал `watch:data-changed`.
2. Каждый инстанс подписан на канал.
3. Подписчик сопоставляет событие с фильтрами слушателей и шлёт `data:changed`
   только тем, чьё окно просмотра пересекается с изменением.
4. Горизонтальное масштабирование: сколько бы инстансов ни было за nginx,
   событие доходит до всех слушателей.

## Модель данных (кратко)

- `users` — системные пользователи (синхронизация из Keycloak)
- `employees` (+ `educations`, `certifications`, `medical_exams`, `ppe_records` со сроками давности)
- `projects` → `fields` (месторождения) → `project_employees` (доступ работников к проектам)
- `employment_periods` — **единая таблица периодов** (тип, время, version, update_reason, active, автор)
- таблицы деталей видов: `shift_details`, `vacation_details`, ... (1:1, собственные поля каждого вида)
- `financial_records` (income/expense: сумма float, описание) + `financial_attachments` (файлы в S3)
- `audit_logs` — insert/update/delete всех таблиц с автором

Новый вид занятости добавляется файлом-модулем в [`src/models/occupancy/`](src/models/occupancy)
с декоратором `@register_occupancy_type` — REST-эндпоинты и live-обновления подхватят его автоматически.

## Структура

```
src/
├── main.py            # FastAPI + Socket.IO + EventBus lifecycle
├── config.py          # настройки из .env
├── database.py        # async engine/session
├── models/            # SQLAlchemy (Base, сущности, модули занятости)
├── schemas/           # Pydantic
├── api/               # deps (auth/права), router, endpoints
├── services/          # auth, permissions, audit, view_service,
│                      # notifications (SMTP), storage (S3), domain_events
└── sockets/           # events (Socket.IO), manager (подписки), events_bus (Redis)
```

Запуск в Docker: `docker compose --profile app up -d` (после сборки образа).