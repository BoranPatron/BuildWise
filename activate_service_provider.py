import asyncio
from app.core.database import get_db
from app.models.user import User
from sqlalchemy import select

async def activate_user():
    async for db in get_db():
        stmt = select(User).where(User.email == 'test-dienstleister@buildwise.de')
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            user.is_active = True
            db.add(user)
            await db.commit()
            print(f"✅ User {user.email} wurde aktiviert!")
        else:
            print("❌ User nicht gefunden!")

if __name__ == "__main__":
    asyncio.run(activate_user()) 