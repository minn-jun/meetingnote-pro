"""DB 에 테이블 7개를 만든다. 이미 있는 테이블은 건드리지 않는다

    python -m app.migrate

DATABASE_URL 이 있으면 그 Postgres(Neon)에, 없으면 로컬 SQLite 에 만든다.
"""
from sqlalchemy import inspect

from app.db import engine, init_db


def main() -> None:
    init_db()
    tables = sorted(inspect(engine).get_table_names())
    print(f"{engine.dialect.name} @ {engine.url.host or engine.url.database}")
    print(f"테이블 {len(tables)}개: {', '.join(tables)}")


if __name__ == "__main__":
    main()
