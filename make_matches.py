import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine import User, engine


def main():
    with Session(engine) as session:
        users = list(session.scalars(select(User)))
        remaining_user_ids = set(user.id for user in users)
        for user in users:
            santa = random.choice(list(remaining_user_ids - {user.id}))
            user.gift_recepient_id = santa
            remaining_user_ids.remove(santa)
        session.commit()


if __name__ == "__main__":
    main()
