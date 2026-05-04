from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from donation_user.repository.db import get_connection


def main() -> None:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DB_NAME() AS db_name, COUNT(*) AS user_count FROM dbo.Users")
        row = cursor.fetchone()
        print(f"Connected to database: {row.db_name}")
        print(f"Users table rows: {row.user_count}")


if __name__ == "__main__":
    main()
