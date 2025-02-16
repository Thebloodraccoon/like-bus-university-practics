from sqlalchemy.orm import Session

from app.models.users import User


def test_database_connection(db_session: Session):
    test_user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        role="polonus_manager",
    )

    db_session.add(test_user)
    db_session.commit()

    retrieved_user = db_session.query(User).filter_by(email="test@example.com").first()

    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.hashed_password == "hashed_password"
    assert retrieved_user.role == "polonus_manager"
