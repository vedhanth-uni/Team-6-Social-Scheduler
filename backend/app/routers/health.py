#Generic endpoint file, you will have to create endpoint files like this for each set of tasks, so : User endpoints, schedule endpoints etc


from fastapi import APIRouter, Depends
from sqlmodel import Session, select 

from app.database import get_session

router = APIRouter(tags = ["Health"])


@router.get("/health")
def health_checker():
    return {"message:" : "WE'RE LIVE!!!"}


@router.get("/health/db")
def database_health_check(session : Session = Depends(get_session)):
    session.exec(select(1)).one()
    return {"message:" : "help me" , 
            "database:" : "connected?",}

