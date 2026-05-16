import json
import sqlite3
from datetime import datetime
from pathlib import Path

from app.schemas import GuestPersona, GuestProfileCreate, GuestProfileRecord

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "rosewood.sqlite"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guest_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guest_name TEXT NOT NULL,
                suite TEXT NOT NULL,
                property_location TEXT NOT NULL DEFAULT 'Rosewood Menlo Park',
                booking_notes TEXT NOT NULL,
                arrival_date TEXT NOT NULL,
                stay_nights INTEGER NOT NULL,
                occasion TEXT,
                persona_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(guest_profiles)").fetchall()
        }
        if "property_location" not in columns:
            connection.execute(
                """
                ALTER TABLE guest_profiles
                ADD COLUMN property_location TEXT NOT NULL DEFAULT 'Rosewood Menlo Park'
                """
            )


def _row_to_profile(row: sqlite3.Row) -> GuestProfileRecord:
    persona = GuestPersona.model_validate(json.loads(row["persona_json"]))
    return GuestProfileRecord(
        id=row["id"],
        guest_name=row["guest_name"],
        suite=row["suite"],
        property_location=row["property_location"],
        booking_notes=row["booking_notes"],
        arrival_date=row["arrival_date"],
        stay_nights=row["stay_nights"],
        occasion=row["occasion"],
        persona=persona,
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def create_guest_profile(profile: GuestProfileCreate) -> GuestProfileRecord:
    init_db()
    now = datetime.utcnow().isoformat()
    persona_json = profile.persona.model_dump_json()

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO guest_profiles (
                guest_name,
                suite,
                property_location,
                booking_notes,
                arrival_date,
                stay_nights,
                occasion,
                persona_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                profile.guest_name,
                profile.suite,
                profile.property_location,
                profile.booking_notes,
                profile.arrival_date,
                profile.stay_nights,
                profile.occasion,
                persona_json,
                now,
                now,
            ),
        )
        row = connection.execute(
            "SELECT * FROM guest_profiles WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()

    return _row_to_profile(row)


def list_guest_profiles() -> list[GuestProfileRecord]:
    init_db()
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM guest_profiles ORDER BY updated_at DESC, id DESC"
        ).fetchall()

    return [_row_to_profile(row) for row in rows]


def get_guest_profile(profile_id: int) -> GuestProfileRecord | None:
    init_db()
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM guest_profiles WHERE id = ?", (profile_id,)
        ).fetchone()

    if row is None:
        return None

    return _row_to_profile(row)
