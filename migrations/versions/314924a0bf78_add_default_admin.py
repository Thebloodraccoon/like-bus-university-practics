"""add default admin

Revision ID: 314924a0bf78
Revises: 25bc2f910262
Create Date: 2025-02-16 21:20:13.494961

"""

from datetime import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Integer
from sqlalchemy.sql import column, table

from app.constants import settings
from app.utils.auth import get_password_hash

# revision identifiers, used by Alembic.
revision: str = "314924a0bf78"
down_revision: Union[str, None] = "25bc2f910262"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


users_table = table(
    "users",
    column("id", Integer),
    column("email", sa.String),
    column("hashed_password", sa.String),
    column("role", sa.String),
    column("created_at", sa.DateTime(timezone=True)),
)

DEFAULT_ADMIN_EMAIL = settings.ADMIN_LOGIN
DEFAULT_ADMIN_PASSWORD = settings.ADMIN_PASSWORD.get_secret_value()


def upgrade() -> None:
    conn = op.get_bind()

    stmt = sa.text("SELECT id FROM users WHERE email = :email")
    admin_exists = (
        conn.execute(stmt, {"email": DEFAULT_ADMIN_EMAIL}).fetchone() is not None
    )

    if admin_exists:
        stmt = sa.text(
            """
                        UPDATE users 
                        SET hashed_password = :hashed_password 
                        WHERE email = :email
                    """
        )
        conn.execute(
            stmt,
            {
                "email": DEFAULT_ADMIN_EMAIL,
                "hashed_password": get_password_hash(DEFAULT_ADMIN_PASSWORD),
            },
        )
    else:
        op.bulk_insert(
            users_table,
            [
                {
                    "email": DEFAULT_ADMIN_EMAIL,
                    "hashed_password": get_password_hash(DEFAULT_ADMIN_PASSWORD),
                    "role": "admin",
                    "created_at": datetime.utcnow(),
                }
            ],
        )


def downgrade() -> None:
    conn = op.get_bind()
    stmt = sa.text("DELETE FROM users WHERE email = :email")
    conn.execute(stmt, {"email": DEFAULT_ADMIN_EMAIL})
