"""Create a separate, restricted runtime database role. Secrets stay in ignored .env.

Run after initial migration. Does not rotate an existing role's credentials.
"""
import secrets
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from knowdoc.config import settings


def main():
    cfg = settings()
    if cfg.migration_database_url:
        print("Restricted role already configured; run migrations and grants after schema changes.")
        return
    admin_url = make_url(cfg.database_url)
    role = "knowdoc_app"
    password = secrets.token_hex(24)
    with create_engine(admin_url).begin() as connection:
        existing = connection.scalar(text("SELECT 1 FROM pg_roles WHERE rolname=:name"), {"name": role})
        if existing:
            raise SystemExit("Role exists but .env is not configured; refusing to rotate existing credentials")
        # Password consists only of generated hexadecimal characters, never user input.
        connection.exec_driver_sql(f"CREATE ROLE {role} LOGIN PASSWORD '{password}' NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT")
        connection.exec_driver_sql(f"GRANT CONNECT ON DATABASE {admin_url.database} TO {role}")
        connection.exec_driver_sql(f"GRANT USAGE ON SCHEMA public TO {role}")
        connection.exec_driver_sql(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {role}")
        connection.exec_driver_sql(f"REVOKE ALL ON alembic_version FROM {role}")
        connection.exec_driver_sql(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {role}")
    env = Path(".env")
    content = env.read_text()
    runtime = admin_url.set(username=role, password=password).render_as_string(hide_password=False)
    lines = [f"DATABASE_URL={runtime}" if line.startswith("DATABASE_URL=") else line for line in content.splitlines()]
    lines += [f"MIGRATION_DATABASE_URL={admin_url.render_as_string(hide_password=False)}", f"DATABASE_APP_PASSWORD={password}"]
    env.write_text("\n".join(lines) + "\n")
    print("Created non-superuser runtime role; stored credentials only in ignored .env.")


if __name__ == "__main__":
    main()
