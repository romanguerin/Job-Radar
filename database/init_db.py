from sqlalchemy.orm import Session

from database.session import Base, engine
from models.entities import User


DEFAULT_USERS = [
    {
        "name": "User 1",
        "categories": "software, data, product",
        "locations": "Paris, Remote, Lyon",
        "keywords": "python, fastapi, data, backend",
        "excluded_keywords": "internship, unpaid, stage",
        "minimum_salary": 45000,
    },
    {
        "name": "User 2",
        "categories": "marketing, sales, operations",
        "locations": "Remote, Bordeaux, Nantes",
        "keywords": "growth, seo, account manager, operations",
        "excluded_keywords": "commission only, freelance only",
        "minimum_salary": 35000,
    },
]


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def seed_default_users(db: Session) -> None:
    for index, defaults in enumerate(DEFAULT_USERS, start=1):
        user = db.get(User, index)
        if user is None:
            db.add(User(id=index, **defaults))
    db.commit()
