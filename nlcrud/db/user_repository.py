"""User repository implementation.

Provides database operations for User entities.
"""
import sqlite3
from typing import List, Optional
from datetime import datetime

from nlcrud.db.models.user import User
from nlcrud.db.repository import Repository, EntityNotFoundError, InvalidEntityError
from nlcrud.logger import get_logger

logger = get_logger("user_repository")


class UserRepository(Repository[User]):
    """Repository for User entities.

    Handles all database operations for users.
    """

    def __init__(self, db_path: str = "db/db.sqlite") -> None:
        """Initialize repository with database connection.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.debug(f"UserRepository initialized with db: {db_path}")

    def create(self, user: User) -> User:
        """Create a new user in the database.

        Args:
            user: User to create

        Returns:
            Created user with ID assigned

        Raises:
            InvalidEntityError: If user is invalid
        """
        logger.debug(f"Creating user: {user.name}")

        try:
            user.validate()
        except ValueError as e:
            logger.error(f"Invalid user data: {e}")
            raise InvalidEntityError(f"Invalid user: {e}") from e

        cursor = self.conn.cursor()
        now = datetime.now()

        cursor.execute(
            """
            INSERT INTO users (name, email, age)
            VALUES (?, ?, ?)
            """,
            (user.name, user.email, user.age),
        )
        self.conn.commit()

        user.id = cursor.lastrowid
        user.created_at = now
        user.updated_at = now

        logger.info(f"Created user with ID: {user.id}")
        return user

    def read(self, user_id: int) -> Optional[User]:
        """Read a user by ID.

        Args:
            user_id: ID of user to retrieve

        Returns:
            User if found, None otherwise
        """
        logger.debug(f"Reading user with ID: {user_id}")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if not row:
            logger.warning(f"User not found: {user_id}")
            return None

        user = self._row_to_user(row)
        logger.debug(f"Retrieved user: {user.name}")
        return user

    def read_all(self) -> List[User]:
        """Read all users from the database.

        Returns:
            List of all users
        """
        logger.debug("Reading all users")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()

        users = [self._row_to_user(row) for row in rows]
        logger.info(f"Retrieved {len(users)} users")
        return users

    def update(self, user_id: int, user: User) -> User:
        """Update an existing user.

        Args:
            user_id: ID of user to update
            user: Updated user data

        Returns:
            Updated user

        Raises:
            EntityNotFoundError: If user not found
            InvalidEntityError: If user is invalid
        """
        logger.debug(f"Updating user {user_id}")

        try:
            user.validate()
        except ValueError as e:
            logger.error(f"Invalid user data: {e}")
            raise InvalidEntityError(f"Invalid user: {e}") from e

        cursor = self.conn.cursor()
        now = datetime.now()

        cursor.execute(
            """
            UPDATE users
            SET name = ?, email = ?, age = ?
            WHERE id = ?
            """,
            (user.name, user.email, user.age, user_id),
        )
        self.conn.commit()

        if cursor.rowcount == 0:
            logger.error(f"User not found: {user_id}")
            raise EntityNotFoundError(f"User not found: {user_id}")

        user.id = user_id
        user.updated_at = now
        logger.info(f"Updated user: {user_id}")
        return user

    def delete(self, user_id: int) -> bool:
        """Delete a user by ID.

        Args:
            user_id: ID of user to delete

        Returns:
            True if user was deleted, False if not found
        """
        logger.debug(f"Deleting user {user_id}")

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        self.conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted user: {user_id}")
        else:
            logger.warning(f"User not found: {user_id}")

        return deleted

    def find(self, **criteria) -> List[User]:
        """Find users matching criteria.

        Args:
            **criteria: Field names and values to match

        Returns:
            List of matching users
        """
        logger.debug(f"Finding users with criteria: {criteria}")

        if not criteria:
            return self.read_all()

        # Build WHERE clause
        where_parts = []
        values = []
        for key, value in criteria.items():
            where_parts.append(f"{key} = ?")
            values.append(value)

        where_clause = " AND ".join(where_parts)
        query = f"SELECT * FROM users WHERE {where_clause}"

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        rows = cursor.fetchall()

        users = [self._row_to_user(row) for row in rows]
        logger.debug(f"Found {len(users)} users matching criteria")
        return users

    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email.

        Args:
            email: Email to search for

        Returns:
            User if found, None otherwise
        """
        users = self.find(email=email)
        return users[0] if users else None

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        """Convert database row to User object.

        Args:
            row: Database row

        Returns:
            User instance
        """
        return User(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            age=row["age"],
        )
