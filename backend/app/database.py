#never make me do this database stuff again

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

BACKEND_DIR = Path(__file__).resolve().parent.parent #we got the backend directory's path now

DATABASE_PATH = BACKEND_DIR / "scheduler.db" # add this scheduler.db to our backend directory

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread" : False}
)

def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session