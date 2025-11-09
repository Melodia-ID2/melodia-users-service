from tests.integral.fixtures.server import TEST_BASE_URL
from tests.integral.fixtures.factories import TestArtist, TestUser
from tests.integral.fixtures.auth import auth_headers

pytest_plugins = [
    "tests.integral.fixtures.db",
    "tests.integral.fixtures.server", 
    "tests.integral.fixtures.factories",
    "tests.integral.fixtures.seed",
    "tests.integral.fixtures.auth",
]

__all__ = [
    "TEST_BASE_URL",
    "TestArtist",
    "TestUser", 
    "auth_headers",
]
