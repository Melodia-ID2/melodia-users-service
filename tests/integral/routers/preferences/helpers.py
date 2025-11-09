from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.useraccount import UserAccount


async def set_user_preferences(session: AsyncSession, user_id: UUID, preferences: int) -> None:
    """Set user preferences and commit to database."""
    result = await session.execute(select(UserAccount).where(UserAccount.id == user_id))
    account = result.scalar_one()
    account.preferences = preferences
    session.add(account)
    await session.commit()


async def get_user_preferences(session: AsyncSession, user_id: UUID) -> int:
    """Get user preferences from database."""
    result = await session.execute(select(UserAccount.preferences).where(UserAccount.id == user_id))
    return result.scalar_one()


def assert_bit_is_set(preferences: int, bit: int) -> None:
    """Assert that a specific bit is set in preferences."""
    assert preferences & bit != 0, f"Expected bit {bit} to be set in preferences {preferences}"


def assert_bit_is_not_set(preferences: int, bit: int) -> None:
    """Assert that a specific bit is not set in preferences."""
    assert preferences & bit == 0, f"Expected bit {bit} to not be set in preferences {preferences}"


def expected_error_response(status: int, detail: str, instance: str) -> dict[str, str | int]:
    """Generate expected error response structure."""
    title_map = {
        401: "Authentication Error",
        404: "Resource Not Found",
        400: "Bad request error",
        422: "Unprocessable Entity",
    }
    return {
        "type": "about:blank",
        "title": title_map.get(status, "Error"),
        "status": status,
        "detail": detail,
        "instance": instance,
    }
