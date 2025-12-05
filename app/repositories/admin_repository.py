from typing import Literal

from sqlalchemy import String, cast
from sqlmodel import Session, case, func, select

from app.models.useraccount import AccountProvider, UserAccount, UserRole
from app.models.usercredential import UserCredential
from app.models.userprofile import UserProfile


SortField = Literal["created_at", "username", "role", "status"]
SortOrder = Literal["asc", "desc"]


def get_all_users(
    session: Session,
    page: int,
    page_size: int,
    role: UserRole | None = None,
    sort_by: SortField = "created_at",
    sort_order: SortOrder = "asc",
):
    subq = (
        select(
            UserCredential.email,
            UserCredential.provider,
            UserCredential.user_id,
            case((UserCredential.provider == AccountProvider.LOCAL, 1), else_=0).label("is_local"),
            func.row_number()
            .over(
                partition_by=UserCredential.user_id,
                order_by=case((UserCredential.provider == AccountProvider.LOCAL, 1), else_=0).desc(),
            )
            .label("rn"),
        )
        .subquery()
    )

    filtered_subq = select(subq).where(subq.c.rn == 1).subquery()

    sort_columns = {
        "created_at": UserAccount.created_at,
        "username": UserProfile.username,
        "role": cast(UserAccount.role, String),
        "status": cast(UserAccount.status, String),
    }

    sort_column = sort_columns.get(sort_by, UserAccount.created_at)
    is_desc = sort_order == "desc"
    primary_sort = sort_column.desc() if is_desc else sort_column
    secondary_created = UserAccount.created_at.desc() if is_desc else UserAccount.created_at
    secondary_id = UserAccount.id.desc() if is_desc else UserAccount.id

    stmt = (
        select(
            UserAccount.id,
            UserProfile.username,
            filtered_subq.c.email,
            UserAccount.role,
            UserAccount.status,
            UserProfile.profile_photo,
        )
        .outerjoin(UserProfile, UserAccount.id == UserProfile.id)
        .outerjoin(filtered_subq, UserAccount.id == filtered_subq.c.user_id)
        .order_by(primary_sort, secondary_created, secondary_id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    if role is not None:
        stmt = stmt.where(UserAccount.role == role)

    users = session.exec(stmt).all()
    count_stmt = select(func.count()).select_from(UserAccount)
    if role is not None:
        count_stmt = count_stmt.where(UserAccount.role == role)
    total = session.scalar(count_stmt)
    return users, total


def delete_user_account(session: Session, account: UserAccount) -> None:
    session.delete(account)
    session.commit()
    return None