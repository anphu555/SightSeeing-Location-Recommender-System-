from sqlmodel import SQLModel, create_engine, Session

# 1. Setup the Database URL (SQLite in this case)
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# 2. Create the Engine
# echo=True prints SQL statements to the console (good for debugging)
engine = create_engine(sqlite_url, echo=False)

# 3. The Function to Create Tables
def create_db_and_tables():
    # This looks at all classes with table=True and creates them in the DB
    SQLModel.metadata.create_all(engine)

# 4. The Dependency for FastAPI
def get_session():
    with Session(engine) as session:
        yield session