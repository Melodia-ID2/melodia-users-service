from sqlmodel import Session, case, func, select

from app.models.useraccount import AccountProvider, UserAccount
from app.models.usercredential import UserCredential
from app.models.userprofile import UserProfile


def get_all_users(session: Session, page: int, page_size: int):
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

    stmt = (
        select(
            UserAccount.id,
            UserProfile.username,
            filtered_subq.c.email,
            UserAccount.role,
            UserAccount.status,
        )
        .outerjoin(UserProfile, UserAccount.id == UserProfile.id)
        .outerjoin(filtered_subq, UserAccount.id == filtered_subq.c.user_id)
        .order_by(UserAccount.created_at)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    users = session.exec(stmt).all()
    total = session.scalar(select(func.count()).select_from(UserAccount))
    return users, total


def delete_user_account(session: Session, account: UserAccount) -> None:
    session.delete(account)
    session.commit()
    return None