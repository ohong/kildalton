from database import Base, engine

def init_db():
    # Create all tables
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
