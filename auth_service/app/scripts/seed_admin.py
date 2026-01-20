import argparse
import asyncio

from app.core.db import AsyncSession, local_session
from app.schemas.auth import UserCreate
from app.services.auth import AuthService
from app.core.config import settings

# import logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


async def seed_admin(db: AsyncSession):
    print("Seeding admin user")
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset", action="store_true", help="Delete existing admin and re-seed"
    )
    args = parser.parse_args()
    from app.models.auth import Role, User, UserRole
    from sqlalchemy import delete, select

    admin_username = settings.ADMIN_USERNAME
    admin_email = settings.ADMIN_EMAIL
    admin_password = settings.ADMIN_PASSWORD

    UserCreate.model_validate(
        {
            "username": admin_username,
            "email": admin_email,
            "password": admin_password,
        }
    )

    # Check if admin user exists
    stmt = select(User).where(User.username == admin_username)
    result = await db.execute(stmt)
    admin = result.scalar_one_or_none()

    if args.reset:
        print("Resetting admin user")
        # TODO: USE on cascade delete instead
        # user_role_stmt = delete(UserRole).where(
        #     UserRole.user_id == admin.id,
        # )
        # user_role_result = await db.execute(user_role_stmt)
        await db.execute(delete(User).where(User.username == admin_username))
        await db.commit()
        admin = None

    if not admin:
        admin = User(
            username=admin_username,
            email=admin_email,
            password_hash=AuthService.hash_password(admin_password),
            is_superuser=True,
            is_active=True,
        )
        db.add(admin)
        await db.flush()
        print("Admin user created")
    else:
        print("Admin user already exists")

    # Fetch admin role
    role_stmt = select(Role).where(Role.name == "admin")
    role_result = await db.execute(role_stmt)
    admin_role = role_result.scalar_one_or_none()

    if not admin_role:
        raise RuntimeError("Admin role not found. Run seed_permissions first.")

    # Check if role already assigned
    user_role_stmt = select(UserRole).where(
        UserRole.user_id == admin.id,
        UserRole.role_id == admin_role.id,
    )
    user_role_result = await db.execute(user_role_stmt)
    existing_user_role = user_role_result.scalar_one_or_none()

    if not existing_user_role:
        db.add(
            UserRole(
                user_id=str(admin.id),
                role_id=str(admin_role.id),
            )
        )
        print("Admin role assigned to admin user")
    else:
        print("Admin role already assigned")

    await db.commit()
    print("Admin seeding complete")


async def main():
    async with local_session() as db:
        await seed_admin(db)


if __name__ == "__main__":
    asyncio.run(main())
