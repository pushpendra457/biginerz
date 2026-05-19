import asyncio
from passlib.context import CryptContext
from sqlalchemy.future import select

# IMPORT FIX: Import the whole module so we get the live, updated variables
from app import database
from app.models.rep import Rep
from app.models.retailer import Retailer

# Initialize the password hashing engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=4)

async def generate_all_passwords():
    print("Connecting to database...")
    await database.connect_db()
    
    # Access the session factory THROUGH the module so it isn't None
    async with database._session_factory() as db:
        print("Fetching Reps and Retailers...")
        
        # 1. Update all Representatives
        reps_result = await db.execute(select(Rep).where(Rep.hashed_password == ""))
        reps = reps_result.scalars().all()
        
        for rep in reps:
            # Creates a password like: Syngenta@REP_001
            plain_password = f"Syngenta@{rep.rep_id}"
            rep.hashed_password = pwd_context.hash(plain_password)
            
        # 2. Update all Retailers
        retailers_result = await db.execute(select(Retailer).where(Retailer.hashed_password == ""))
        retailers = retailers_result.scalars().all()
        
        for retailer in retailers:
            # Creates a password like: Syngenta@RTL_001
            plain_password = f"Syngenta@{retailer.retailer_id}"
            retailer.hashed_password = pwd_context.hash(plain_password)

        # 3. Save all changes to the database at once
        await db.commit()
        
        print(f"✅ Success! Generated secure passwords for {len(reps)} Reps and {len(retailers)} Retailers.")

    await database.disconnect_db()

if __name__ == "__main__":
    import sys
    
    # Windows-specific fix for the psycopg async driver
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    # Run the async function
    asyncio.run(generate_all_passwords())