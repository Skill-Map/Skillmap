import asyncio
from argon2 import PasswordHasher
from database import AsyncSessionLocal
import models

# Инициализация хэшировщика Argon2
pwd_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return pwd_hasher.hash(password)

async def main():
    email = "admin@skillmap.ru"
    password = "admin123"

    async with AsyncSessionLocal() as db:
        admin = models.User(
            email=email,
            password=hash_password(password),  # <- используем правильное поле
            type="admin",
            active=True,
            name="Admin",
            surname="System",
            super_permissions=True,  # Можно сразу дать супер права
            can_manage_roles=True,
            can_manage_billing=True,
            can_impersonate=True
        )
        db.add(admin)
        await db.flush()
        await db.commit()
        print("✅ Admin created:", email, password)

if __name__ == "__main__":
    asyncio.run(main())
