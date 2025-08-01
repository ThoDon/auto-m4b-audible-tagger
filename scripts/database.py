#!/usr/bin/env python3
"""
Database module for tracking audiobooks and their processing status
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class AudiobookDatabase:
    """SQLite database for tracking audiobooks"""

    def __init__(self, db_path: str = "audiobooks.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._init_database()

    def _init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create audiobooks table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS audiobooks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_hash TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP NULL,
                    metadata TEXT NULL,
                    cover_path TEXT NULL,
                    final_path TEXT NULL,
                    error_message TEXT NULL
                )
            """
            )

            # Create search_sessions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS search_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    file_id TEXT NOT NULL,
                    search_results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (file_id) REFERENCES audiobooks (file_id)
                )
            """
            )

            # Create indexes
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_audiobooks_status ON audiobooks(status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_audiobooks_file_path ON audiobooks(file_path)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_search_sessions_file_id ON search_sessions(file_id)"
            )

            conn.commit()

    def add_audiobook(self, file_path: Path, file_id: str) -> bool:
        """Add a new audiobook to the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if file already exists
                cursor.execute(
                    "SELECT file_id FROM audiobooks WHERE file_path = ?",
                    (str(file_path),),
                )
                existing = cursor.fetchone()

                if existing:
                    self.logger.info(f"File already in database: {file_path}")
                    return True

                # Add new file
                cursor.execute(
                    """
                    INSERT INTO audiobooks (file_id, file_path, file_name, file_size, file_hash, status)
                    VALUES (?, ?, ?, ?, NULL, 'pending')
                """,
                    (file_id, str(file_path), file_path.name, file_path.stat().st_size),
                )

                conn.commit()
                self.logger.info(
                    f"Added audiobook to database: {file_path} -> {file_id}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Error adding audiobook to database: {e}")
            return False

    def get_audiobook(self, file_id: str) -> Optional[Dict]:
        """Get audiobook by file_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM audiobooks WHERE file_id = ?
                """,
                    (file_id,),
                )

                row = cursor.fetchone()
                if row:
                    return dict(row)
                return None

        except Exception as e:
            self.logger.error(f"Error getting audiobook {file_id}: {e}")
            return None

    def get_all_audiobooks(self, status: Optional[str] = None) -> List[Dict]:
        """Get all audiobooks, optionally filtered by status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                if status:
                    cursor.execute(
                        """
                        SELECT * FROM audiobooks WHERE status = ? ORDER BY created_at DESC
                    """,
                        (status,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM audiobooks ORDER BY created_at DESC
                    """
                    )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Error getting audiobooks: {e}")
            return []

    def update_audiobook_status(
        self,
        file_id: str,
        status: str,
        metadata: Optional[Dict] = None,
        cover_path: Optional[str] = None,
        final_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update audiobook status and metadata"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [status]

                if status == "processed":
                    update_fields.append("processed_at = CURRENT_TIMESTAMP")

                if metadata:
                    update_fields.append("metadata = ?")
                    params.append(str(metadata))

                if cover_path:
                    update_fields.append("cover_path = ?")
                    params.append(cover_path)

                if final_path:
                    update_fields.append("final_path = ?")
                    params.append(final_path)

                if error_message:
                    update_fields.append("error_message = ?")
                    params.append(error_message)

                params.append(file_id)

                cursor.execute(
                    f"""
                    UPDATE audiobooks SET {', '.join(update_fields)}
                    WHERE file_id = ?
                """,
                    params,
                )

                conn.commit()
                self.logger.info(f"Updated audiobook {file_id} status to {status}")
                return True

        except Exception as e:
            self.logger.error(f"Error updating audiobook {file_id}: {e}")
            return False

    def save_search_session(
        self, session_id: str, file_id: str, search_results: List[Dict]
    ) -> bool:
        """Save search session results"""
        try:
            import json

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO search_sessions (session_id, file_id, search_results)
                    VALUES (?, ?, ?)
                """,
                    (session_id, file_id, json.dumps(search_results)),
                )

                conn.commit()
                self.logger.info(
                    f"Saved search session {session_id} for file {file_id}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Error saving search session: {e}")
            return False

    def get_search_session(self, session_id: str) -> Optional[Dict]:
        """Get search session by session_id"""
        try:
            import json

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT * FROM search_sessions WHERE session_id = ?
                """,
                    (session_id,),
                )

                row = cursor.fetchone()
                if row:
                    data = dict(row)
                    data["search_results"] = json.loads(data["search_results"])
                    return data
                return None

        except Exception as e:
            self.logger.error(f"Error getting search session {session_id}: {e}")
            return None

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old search sessions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    DELETE FROM search_sessions 
                    WHERE created_at < datetime('now', '-{} hours')
                """.format(
                        max_age_hours
                    )
                )

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old search sessions")

                return deleted_count

        except Exception as e:
            self.logger.error(f"Error cleaning up old sessions: {e}")
            return 0

    def verify_file_exists(self, file_id: str) -> bool:
        """Verify that the file still exists on disk"""
        try:
            audiobook = self.get_audiobook(file_id)
            if not audiobook:
                return False

            file_path = Path(audiobook["file_path"])
            return file_path.exists()

        except Exception as e:
            self.logger.error(f"Error verifying file {file_id}: {e}")
            return False
