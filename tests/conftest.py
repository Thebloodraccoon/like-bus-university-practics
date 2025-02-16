import pytest
import redis
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.constants import settings
from app.db import Base, get_db, get_redis
from app.main import app
from app.models import User
from app.utils.auth import get_password_hash

engine = create_engine(settings.TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    session = TestingSessionLocal()
    try:
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(scope="function")
def client(override_get_db, override_get_redis):
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def redis_test():

    redis_client = redis.Redis(
        host=settings.TEST_HOST_REDIS,
        port=settings.TEST_PORT_REDIS,
        db=settings.TEST_DB_REDIS,
        decode_responses=True,
    )

    redis_client.flushdb()

    yield redis_client

    redis_client.flushdb()


@pytest.fixture(scope="function")
def override_get_redis(redis_test):
    def _override_get_redis():
        yield redis_test

    app.dependency_overrides[get_redis] = _override_get_redis


@pytest.fixture
def create_user(db_session):
    def _create_user(
        email="test@example.com", password="testpassword123", role="polonus_manager"
    ):
        existing_user = db_session.query(User).filter_by(email=email).first()
        if existing_user:
            return existing_user

        user = User(email=email, hashed_password=get_password_hash(password), role=role)

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    return _create_user


@pytest.fixture
def test_user(create_user):
    return create_user()


@pytest.fixture
def test_admin(create_user):
    return create_user(
        email="admin@example.com",
        password="default_password",
        role="admin",
    )


@pytest.fixture
def get_auth_token(client):
    def _get_auth_token(user, password):
        response = client.post(
            "/auth/login", json={"email": user.email, "password": password}
        )

        access_token = response.json()["access_token"]
        return HTTPAuthorizationCredentials(scheme="Bearer", credentials=access_token)

    return _get_auth_token


@pytest.fixture
def test_user_token(get_auth_token, test_user):
    return get_auth_token(test_user, "testpassword123")


@pytest.fixture
def test_admin_token(get_auth_token, test_admin):
    return get_auth_token(test_admin, "default_password")
