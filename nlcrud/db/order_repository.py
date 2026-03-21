"""Order repository implementation.

Provides database operations for Order entities.
"""
import sqlite3
from typing import List, Optional
from datetime import datetime

from nlcrud.db.models.order import Order
from nlcrud.db.repository import Repository, EntityNotFoundError, InvalidEntityError
from nlcrud.logger import get_logger

logger = get_logger("order_repository")


class OrderRepository(Repository[Order]):
    """Repository for Order entities.

    Handles all database operations for orders.
    """

    def __init__(self, db_path: str = "db/db.sqlite") -> None:
        """Initialize repository with database connection.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.debug(f"OrderRepository initialized with db: {db_path}")

    def create(self, order: Order) -> Order:
        """Create a new order in the database.

        Args:
            order: Order to create

        Returns:
            Created order with ID assigned

        Raises:
            InvalidEntityError: If order is invalid
        """
        logger.debug(f"Creating order for user {order.user_id} with amount {order.amount}")

        try:
            order.validate()
        except ValueError as e:
            logger.error(f"Invalid order data: {e}")
            raise InvalidEntityError(f"Invalid order: {e}") from e

        cursor = self.conn.cursor()
        now = datetime.now()

        cursor.execute(
            """
            INSERT INTO orders (user_id, amount)
            VALUES (?, ?)
            """,
            (order.user_id, order.amount),
        )
        self.conn.commit()

        order.id = cursor.lastrowid
        order.created_at = now
        order.updated_at = now

        logger.info(f"Created order with ID: {order.id}")
        return order

    def read(self, order_id: int) -> Optional[Order]:
        """Read an order by ID.

        Args:
            order_id: ID of order to retrieve

        Returns:
            Order if found, None otherwise
        """
        logger.debug(f"Reading order with ID: {order_id}")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = cursor.fetchone()

        if not row:
            logger.warning(f"Order not found: {order_id}")
            return None

        order = self._row_to_order(row)
        logger.debug(f"Retrieved order: {order.id}")
        return order

    def read_all(self) -> List[Order]:
        """Read all orders from the database.

        Returns:
            List of all orders
        """
        logger.debug("Reading all orders")

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM orders")
        rows = cursor.fetchall()

        orders = [self._row_to_order(row) for row in rows]
        logger.info(f"Retrieved {len(orders)} orders")
        return orders

    def update(self, order_id: int, order: Order) -> Order:
        """Update an existing order.

        Args:
            order_id: ID of order to update
            order: Updated order data

        Returns:
            Updated order

        Raises:
            EntityNotFoundError: If order not found
            InvalidEntityError: If order is invalid
        """
        logger.debug(f"Updating order {order_id}")

        try:
            order.validate()
        except ValueError as e:
            logger.error(f"Invalid order data: {e}")
            raise InvalidEntityError(f"Invalid order: {e}") from e

        cursor = self.conn.cursor()
        now = datetime.now()

        cursor.execute(
            """
            UPDATE orders
            SET user_id = ?, amount = ?
            WHERE id = ?
            """,
            (order.user_id, order.amount, order_id),
        )
        self.conn.commit()

        if cursor.rowcount == 0:
            logger.error(f"Order not found: {order_id}")
            raise EntityNotFoundError(f"Order not found: {order_id}")

        order.id = order_id
        order.updated_at = now
        logger.info(f"Updated order: {order_id}")
        return order

    def delete(self, order_id: int) -> bool:
        """Delete an order by ID.

        Args:
            order_id: ID of order to delete

        Returns:
            True if order was deleted, False if not found
        """
        logger.debug(f"Deleting order {order_id}")

        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        self.conn.commit()

        deleted = cursor.rowcount > 0
        if deleted:
            logger.info(f"Deleted order: {order_id}")
        else:
            logger.warning(f"Order not found: {order_id}")

        return deleted

    def find(self, **criteria) -> List[Order]:
        """Find orders matching criteria.

        Args:
            **criteria: Field names and values to match

        Returns:
            List of matching orders
        """
        logger.debug(f"Finding orders with criteria: {criteria}")

        if not criteria:
            return self.read_all()

        # Build WHERE clause
        where_parts = []
        values = []
        for key, value in criteria.items():
            where_parts.append(f"{key} = ?")
            values.append(value)

        where_clause = " AND ".join(where_parts)
        query = f"SELECT * FROM orders WHERE {where_clause}"

        cursor = self.conn.cursor()
        cursor.execute(query, values)
        rows = cursor.fetchall()

        orders = [self._row_to_order(row) for row in rows]
        logger.debug(f"Found {len(orders)} orders matching criteria")
        return orders

    def find_by_user(self, user_id: int) -> List[Order]:
        """Find all orders for a user.

        Args:
            user_id: User ID to search for

        Returns:
            List of orders for the user
        """
        return self.find(user_id=user_id)

    @staticmethod
    def _row_to_order(row: sqlite3.Row) -> Order:
        """Convert database row to Order object.

        Args:
            row: Database row

        Returns:
            Order instance
        """
        return Order(
            id=row["id"],
            user_id=row["user_id"],
            amount=row["amount"],
        )
