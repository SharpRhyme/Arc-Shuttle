"""SQLite storage helpers for Arc-Shuttle player records.

The database file lives beside this module by default.  Call ``init_db()``
once during application startup before using the player functions.
"""

import csv
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional


DB_PATH = Path(__file__).with_name("arc_shuttle.db")


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Yield a connection that commits/rolls back and is always closed."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        # sqlite3's context manager handles transactions but does not close the
        # connection, so close it explicitly after the transaction completes.
        with connection:
            yield connection
    finally:
        connection.close()


def _as_dict(row: Optional[sqlite3.Row]) -> Optional[dict]:
    """Convert a SQLite row to a regular dictionary for callers."""
    return dict(row) if row is not None else None


def init_db() -> None:
    """Create the players and match-history tables when they are missing."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                rating INTEGER NOT NULL DEFAULT 1200,
                matches_played INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY,
                team_1_p1 TEXT NOT NULL,
                team_1_p2 TEXT,
                team_2_p1 TEXT NOT NULL,
                team_2_p2 TEXT,
                team_1_score INTEGER NOT NULL,
                team_2_score INTEGER NOT NULL,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def log_match(
    team_1_p1: str,
    team_1_p2: Optional[str],
    team_2_p1: str,
    team_2_p2: Optional[str],
    team_1_score: int,
    team_2_score: int,
    timestamp: Optional[str] = None,
) -> Optional[int]:
    """Record a completed match and return its ID, or ``None`` on database error.

    Teammate names may be ``None`` for singles. If no timestamp is supplied,
    SQLite records the insertion time using its ``CURRENT_TIMESTAMP`` default.
    """
    values = (team_1_p1, team_1_p2, team_2_p1, team_2_p2, team_1_score, team_2_score)
    try:
        with _connect() as connection:
            if timestamp is None:
                cursor = connection.execute(
                    """INSERT INTO matches
                       (team_1_p1, team_1_p2, team_2_p1, team_2_p2,
                        team_1_score, team_2_score)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    values,
                )
            else:
                cursor = connection.execute(
                    """INSERT INTO matches
                       (team_1_p1, team_1_p2, team_2_p1, team_2_p2,
                        team_1_score, team_2_score, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (*values, timestamp),
                )
            return cursor.lastrowid
    except sqlite3.Error as error:
        # Keep storage failures visible to the caller without crashing the app.
        print(f"Could not log match: {error}")
        return None


def export_leaderboard_to_csv(filename: str = "rankings.csv") -> bool:
    """Export players ordered by rating (then name) to a CSV file.

    Returns ``True`` on success and ``False`` if the database or file cannot
    be read/written. UTF-8 with a BOM helps spreadsheet applications recognize
    player names correctly.
    """
    try:
        with _connect() as connection:
            players = connection.execute(
                """SELECT id, name, rating, matches_played FROM players
                   ORDER BY rating DESC, name ASC"""
            ).fetchall()

        # newline="" is recommended by csv so it can manage line endings itself.
        with open(filename, "w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(("id", "name", "rating", "matches_played"))
            writer.writerows(tuple(player) for player in players)
        return True
    except (sqlite3.Error, OSError, csv.Error) as error:
        print(f"Could not export leaderboard: {error}")
        return False


def display_leaderboard() -> None:
    """Print the ten highest-rated players in a color-coded Rich table."""
    try:
        with _connect() as connection:
            players = connection.execute(
                """SELECT name, rating, matches_played FROM players
                   ORDER BY rating DESC, name ASC LIMIT 10"""
            ).fetchall()
    except sqlite3.Error as error:
        print(f"Could not load leaderboard: {error}")
        return

    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        print("Rich is required to display the leaderboard. Install it with: pip install rich")
        return

    table = Table(title="Arc-Shuttle Leaderboard", header_style="bold cyan")
    table.add_column("Rank", justify="right", style="dim")
    table.add_column("Player", style="bold")
    table.add_column("Rating", justify="right", style="green")
    table.add_column("Matches", justify="right", style="yellow")

    for rank, player in enumerate(players, start=1):
        table.add_row(
            str(rank), player["name"], str(player["rating"]), str(player["matches_played"])
        )

    Console().print(table)


def add_player(name: str) -> Optional[dict]:
    """Add a player and return their record, or ``None`` if the name exists.

    The name is bound as a SQL parameter; it is never interpolated into SQL.
    """
    try:
        with _connect() as connection:
            cursor = connection.execute(
                "INSERT INTO players (name) VALUES (?)", (name,)
            )
            row = connection.execute(
                "SELECT id, name, rating, matches_played FROM players WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
            return _as_dict(row)
    except sqlite3.IntegrityError:
        # The UNIQUE constraint rejects duplicate names (and NOT NULL rejects None).
        return None


def get_player(name: str) -> Optional[dict]:
    """Return a player's record by name, or ``None`` when no player matches."""
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, name, rating, matches_played FROM players WHERE name = ?",
            (name,),
        ).fetchone()
        return _as_dict(row)


def update_rating(name: str, new_rating: int) -> bool:
    """Set a player's rating; return whether a player with that name existed."""
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE players SET rating = ? WHERE name = ?", (new_rating, name)
        )
        return cursor.rowcount > 0


def increment_matches(name: str) -> bool:
    """Increase a player's match count by one; return whether they existed."""
    with _connect() as connection:
        cursor = connection.execute(
            "UPDATE players SET matches_played = matches_played + 1 WHERE name = ?",
            (name,),
        )
        return cursor.rowcount > 0
