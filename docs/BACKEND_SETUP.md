# Sprint 2 backend setup (Windows / PowerShell)

The backend is **PASS for the agreed Sprint 2 scope**. The operator verified
PostgreSQL 17 migrations and API persistence on port 8001; see
[acceptance evidence and limitations](SPRINT2_ACCEPTANCE.md). It uses a separate
Python environment and imports no sensor code. Automated tests use in-memory SQLite.
The setup instructions below reproduce installation; do not recreate the existing
role/database or reinstall PostgreSQL on this verified laptop.
Authentication is deliberately deferred by the current task. Bind to loopback,
use local script clients, and do not expose this API through a proxy or network.
Local processes can read/write the API without credentials. No frontend or ML
is included, and no service is started automatically.

## Python dependencies

Run from `C:\Users\yuvas\Desktop\NetSentinel`. The continuation has already
installed the backend dependencies in `.venv-backend`; these commands reproduce
that setup on a fresh checkout. Preserve the sensor's existing `.venv`.

```powershell
py -3.11 -m venv .venv-backend
.\.venv-backend\Scripts\python.exe -m pip install -r requirements-backend.txt
.\.venv-backend\Scripts\python.exe backend/manage.py test backend/tests --settings=config.test_settings
.\.venv-backend\Scripts\python.exe backend/manage.py check --settings=config.test_settings
.\.venv-backend\Scripts\python.exe backend/manage.py makemigrations --check --dry-run --settings=config.test_settings
```

Pinned and installed: Django 5.2.17, DRF 3.17.2, psycopg/psycopg-binary 3.3.5,
python-dotenv 1.2.3, with transitive pins in `requirements-backend.txt`.
Django 5.2 supports Python 3.11 and PostgreSQL 14+; see the official
[Django 5.2 release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/)
and [database requirements](https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes).
The test settings reject runtime commands such as runserver, shell and migrate;
normal settings have no SQLite fallback.

## Install PostgreSQL manually after code checks

1. Download the PostgreSQL 17 Windows x64 installer through the
   [official Windows download page](https://www.postgresql.org/download/windows/).
   Install PostgreSQL Server and Command Line Tools. pgAdmin is optional;
   Stack Builder/additional packages are unnecessary for this backend.
2. Keep port `5432` unless already occupied. Choose your own administrator
   password for the `postgres` account and retain it privately. Finish the
   installer and confirm its PostgreSQL Windows service is running. No installer,
   service registration, firewall change or elevation is performed by the repo.
3. Open the local administrative SQL prompt (adjust the version directory if
   you installed another supported major version):

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -h 127.0.0.1 -p 5432 -U postgres -d postgres
```

Create a dedicated local database owner. Enter the following at the **psql**
prompt, not PowerShell. `\password` asks for the password without placing it in
SQL history; see the [psql documentation](https://www.postgresql.org/docs/18/app-psql.html).
Run these creation statements once; do not drop an existing database to repeat setup.

```sql
CREATE ROLE netsentinel LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password netsentinel
CREATE DATABASE netsentinel OWNER netsentinel;
\q
```

Verify the dedicated login:

```powershell
& 'C:\Program Files\PostgreSQL\17\bin\psql.exe' -h 127.0.0.1 -p 5432 -U netsentinel -d netsentinel -c 'SELECT current_database(), current_user;'
```

## Local environment and startup

Copy the template only if `.env` does not already exist:

```powershell
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
.\.venv-backend\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(64))"
notepad .env
```

Put the generated random value in `DJANGO_SECRET_KEY` and your dedicated role's
password in `POSTGRES_PASSWORD`. Do not use the example placeholders. Single-quote
passwords containing spaces or `#` in the `.env` file. Variable interpolation is
disabled, so `$` is preserved. Existing environment variables override `.env`.

| Variable | Required / default |
| --- | --- |
| DJANGO_SECRET_KEY | Required; at least 50 characters, no placeholder accepted |
| POSTGRES_DB | Required; `netsentinel` in the template |
| POSTGRES_USER | Required; `netsentinel` in the template |
| POSTGRES_PASSWORD | Required; no placeholder accepted |
| POSTGRES_HOST | Default `127.0.0.1` |
| POSTGRES_PORT | Default `5432` |
| POSTGRES_SSLMODE | Default `prefer`; local PostgreSQL connection policy |
| DJANGO_DEBUG | Default `false`; leave false for ordinary use |

Missing required configuration fails with the variable's name, not its value.
Database connection failures return 503 from the API without credentials or
driver details. Health checks database connectivity, not migration completeness.
Apply migrations before starting:

```powershell
.\.venv-backend\Scripts\python.exe backend/manage.py check
.\.venv-backend\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
.\.venv-backend\Scripts\python.exe backend/manage.py migrate
.\.venv-backend\Scripts\python.exe backend/manage.py runserver 127.0.0.1:8001
```

In another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/v1/health/
```

Expect `status=ok` and `database=reachable`. API examples and fields are in
[API_PLAN.md](API_PLAN.md). The existing sensor does not upload automatically;
a separated adapter is future work. Do not relabel fabricated test records LIVE.

## Tests, cleanup and outstanding validation

```powershell
.\.venv-backend\Scripts\python.exe backend/manage.py test backend/tests --settings=config.test_settings
.\.venv\Scripts\python.exe -m unittest discover -s tests/sensor -v
git diff --check
```

SQLite tests apply all real migration files to a temporary database. A PostgreSQL
test run needs a separately configured test database/role permitted to create
the test database; do not grant extra privileges to the ordinary runtime role
just to run tests. Migrations and sequential API persistence/retries are now
operator-verified on PostgreSQL 17. Concurrent ingestion and full PostgreSQL
negative-path testing remain unverified; SQLite tests do not certify them.

Explicit routine cleanup on the configured PostgreSQL database:

```powershell
.\.venv-backend\Scripts\python.exe backend/manage.py prune_telemetry
```

Each invocation deletes at most 1,000 rows from each of samples, windows and
status whose receipt time is over 24 hours old; session manifests remain.
No automatic scheduler, global storage-admission budget or durable upload spool
is implemented in this initial scope. Repeat cleanup as appropriate for observed
volume. Idempotency applies while a record is retained; expiry discards its digest
too. Recent endpoints independently restrict observation time to the last 24 hours.
This is a local development backend, not a deployed or authenticated service.
