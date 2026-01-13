import asyncio

from app.core.db import AsyncSession, local_session


async def seed_permissions(db: AsyncSession):
    """Seed initial permissions for all services"""
    print("Seed initial permissions for all services")
    from app.models.auth import Permission, Role, RolePermission
    from sqlalchemy import select

    permissions_data = [
        # Employee Management Permissions
        {"resource": "employee", "action": "read", "description": "Read employee data"},
        {
            "resource": "employee",
            "action": "write",
            "description": "Create/Update employees",
        },
        {"resource": "employee", "action": "delete", "description": "Delete employees"},
        {"resource": "department", "action": "read", "description": "Read departments"},
        {
            "resource": "department",
            "action": "write",
            "description": "Manage departments",
        },
        # Payroll Permissions
        {"resource": "payroll", "action": "read", "description": "View payroll data"},
        {"resource": "payroll", "action": "write", "description": "Process payroll"},
        {"resource": "payroll", "action": "approve", "description": "Approve payroll"},
        # Time & Attendance Permissions
        {"resource": "attendance", "action": "read", "description": "View attendance"},
        {
            "resource": "attendance",
            "action": "write",
            "description": "Record attendance",
        },
        {"resource": "leave", "action": "read", "description": "View leave requests"},
        {
            "resource": "leave",
            "action": "write",
            "description": "Create leave requests",
        },
        {
            "resource": "leave",
            "action": "approve",
            "description": "Approve leave requests",
        },
        # User Management Permissions
        {"resource": "user", "action": "read", "description": "View users"},
        {"resource": "user", "action": "write", "description": "Manage users"},
        {"resource": "role", "action": "read", "description": "View roles"},
        {"resource": "role", "action": "write", "description": "Manage roles"},
    ]

    created_permissions = []

    for perm_data in permissions_data:
        # Check if permission exists
        stmt = select(Permission).where(
            Permission.resource == perm_data["resource"],
            Permission.action == perm_data["action"],
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            permission = Permission(**perm_data)
            db.add(permission)
            created_permissions.append(permission)

    await db.commit()

    # Create default roles
    roles_data = [
        {
            "name": "admin",
            "description": "System administrator",
            "permissions": ["*:*"],  # All permissions
        },
        {
            "name": "hr_manager",
            "description": "HR Manager",
            "permissions": [
                "employee:read",
                "employee:write",
                "employee:delete",
                "department:read",
                "department:write",
                "payroll:read",
                "payroll:write",
                "attendance:read",
                "leave:approve",
            ],
        },
        {
            "name": "employee",
            "description": "Regular Employee",
            "permissions": [
                "employee:read",  # Can read own profile
                "attendance:write",  # Can clock in/out
                "leave:write",  # Can request leave
            ],
        },
        {
            "name": "payroll_specialist",
            "description": "Payroll Specialist",
            "permissions": [
                "employee:read",
                "payroll:read",
                "payroll:write",
                "attendance:read",
            ],
        },
    ]

    for role_data in roles_data:
        stmt = select(Role).where(Role.name == role_data["name"])
        result = await db.execute(stmt)
        existing_role = result.scalar_one_or_none()

        if not existing_role:
            role = Role(name=role_data["name"], description=role_data["description"])
            db.add(role)
            await db.flush()

            # Assign permissions to role
            for perm_string in role_data["permissions"]:
                if perm_string == "*:*":
                    # Assign all permissions
                    all_perms_stmt = select(Permission)
                    all_perms_result = await db.execute(all_perms_stmt)
                    all_permissions = all_perms_result.scalars().all()

                    for permission in all_permissions:
                        role_perm = RolePermission(
                            role_id=str(role.id), permission_id=str(permission.id)
                        )
                        db.add(role_perm)
                else:
                    resource, action = perm_string.split(":")
                    perm_stmt = select(Permission).where(
                        Permission.resource == resource, Permission.action == action
                    )
                    perm_result = await db.execute(perm_stmt)
                    permission = perm_result.scalar_one_or_none()

                    if permission:
                        role_perm = RolePermission(
                            role_id=str(role.id), permission_id=str(permission.id)
                        )
                        db.add(role_perm)

    await db.commit()
    print("Permissions and roles seeded successfully!")


async def main():
    async with local_session() as db:
        await seed_permissions(db)


if __name__ == "__main__":
    asyncio.run(main())
