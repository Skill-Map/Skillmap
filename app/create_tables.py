#!/usr/bin/env python3
# create_tables.py
import asyncio
import sys
import os
from database import engine
import models

async def create_tables():
    try:
        print("🔧 Creating database tables...")
        async with engine.begin() as conn:
            await conn.run_sync(models.Base.metadata.create_all)
        print("✅ Tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)