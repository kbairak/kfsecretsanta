import random
import string
from typing import Annotated

from fastapi import Cookie, FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from h import button, code, form, fragment, h1, h2, h3, input, li, p, pre, textarea, ul


class Base(DeclarativeBase):
    pass


def _random_string():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(6), default=_random_string, primary_key=True)
    fullname: Mapped[str]
    delivery_instructions: Mapped[str]
    gift_recepient_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    gift_recepient: Mapped["User | None"] = relationship(
        back_populates="gift_giver", remote_side=[id]
    )
    gift_giver: Mapped["User | None"] = relationship(back_populates="gift_recepient")


engine = create_engine("sqlite:///secretsanta.db")
Base.metadata.create_all(engine)

app = FastAPI()


@app.get("/")
def root(secretsanta_id: Annotated[str | None, Cookie()] = None):
    with Session(engine) as session:
        if user := session.scalars(
            select(User).where(User.id == secretsanta_id)
        ).first():
            matchmaking_made = bool(
                session.scalars(
                    select(User).where(User.gift_recepient_id != None).limit(1)
                ).first()
            )
            return HTMLResponse(
                str(
                    fragment[
                        (
                            form(action="/make_matches", method="post")[
                                button["Create matches"]
                            ]
                            if user.fullname == "kbairak"
                            else ""
                        ),
                        form(action="/logout", method="post")[button["Log out"]],
                        (
                            form(action="/remove_me", method="post")[
                                button["Remove myself"]
                            ]
                            if not matchmaking_made
                            else ""
                        ),
                        h1[f"Welcome {user.fullname}"],
                        p[
                            "Your ID is ",
                            code[user.id],
                            ", write it down in case you log out or log in from "
                            "another browser",
                        ],
                        *(
                            [
                                h2[
                                    "You have to buy a present for "
                                    f"{user.gift_recepient.fullname}"
                                ],
                                h3["Delivery instructions"],
                                pre[user.gift_recepient.delivery_instructions],
                            ]
                            if user.gift_recepient
                            else []
                        ),
                        h2["Change details"],
                        form(action="/edit_user", method="post")[
                            p[
                                "Your name: ",
                                input(name="fullname", value=user.fullname),
                            ],
                            p[
                                "Delivery instructions: ",
                                textarea(
                                    name="delivery_instructions",
                                    required="required",
                                    rows=4,
                                    cols=80,
                                )[user.delivery_instructions],
                            ],
                            p[button["Save"]],
                        ],
                        h2["The participants are:"],
                        ul[
                            *[
                                li[user.fullname]
                                for user in session.scalars(select(User))
                            ]
                        ],
                    ]
                )
            )
        else:
            return HTMLResponse(
                str(
                    fragment[
                        h3[
                            "Did you sign up from a different browser or logged out? "
                            "Log in again using your user ID:"
                        ],
                        form(action="/login", method="post")[
                            p[
                                "User ID: ",
                                input(name="id", required="required"),
                                button["Log in"],
                            ]
                        ],
                        h2["Sign up"],
                        form(action="/signup", method="post")[
                            p[
                                "Your name: ",
                                input(name="fullname", required="required"),
                            ],
                            p[
                                "Delivery instructions (address, BoxNow box, email, "
                                "phone number): ",
                                textarea(
                                    name="delivery_instructions",
                                    required="required",
                                    rows=4,
                                    cols=80,
                                )[
                                    "Adress: \nEmail: \nPhone number: \nBox now locker: "
                                ],
                            ],
                            p[button["Signup"]],
                        ],
                    ]
                )
            )


@app.post("/signup")
def signup(
    fullname: Annotated[str, Form()], delivery_instructions: Annotated[str, Form()]
):
    with Session(engine) as session:
        if session.scalars(select(User).where(User.fullname == fullname)).first():
            return HTMLResponse("This name already exists", status_code=409)
        session.add(
            user := User(fullname=fullname, delivery_instructions=delivery_instructions)
        )
        session.commit()
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("secretsanta_id", user.id)
        return response


@app.post("/login")
def login(id: Annotated[str, Form()]):
    with Session(engine) as session:
        if user := session.scalars(select(User).where(User.id == id)).first():
            response = RedirectResponse("/", status_code=302)
            response.set_cookie("secretsanta_id", user.id)
            return response
        else:
            return HTMLResponse("User not found", status_code=404)


@app.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("secretsanta_id")
    return response


@app.post("/remove_me")
def remove_me(secretsanta_id: Annotated[str, Cookie()]):
    with Session(engine) as session:
        if bool(
            session.scalars(
                select(User).where(User.gift_recepient_id != None).limit(1)
            ).first()
        ):
            return HTMLResponse(
                "You can't remove yourself after matchmaking has been made",
                status_code=403,
            )
        if user := session.scalars(
            select(User).where(User.id == secretsanta_id)
        ).first():
            session.delete(user)
            session.commit()
            response = RedirectResponse("/", status_code=302)
            response.delete_cookie("secretsanta_id")
            return response
        else:
            return HTMLResponse("User not found", status_code=404)


@app.post("/make_matches")
def make_matches(secretsanta_id: Annotated[str, Cookie()]):
    with Session(engine) as session:
        matchmaking_made = bool(
            session.scalars(
                select(User).where(User.gift_recepient_id != None).limit(1)
            ).first()
        )
        if matchmaking_made:
            return HTMLResponse("Matches have already been made", status_code=403)
        if not session.scalars(
            select(User).where(User.id == secretsanta_id, User.fullname == "kbairak")
        ).first():
            return HTMLResponse("You are not allowed to make matches", status_code=403)

        users = list(session.scalars(select(User)))
        remaining_user_ids = set(user.id for user in users)
        for user in users:
            santa = random.choice(list(remaining_user_ids - {user.id}))
            user.gift_recepient_id = santa
            remaining_user_ids.remove(santa)
        session.commit()
        return RedirectResponse("/", status_code=302)


@app.post("/edit_user")
def edit_user(
    secretsanta_id: Annotated[str, Cookie()],
    fullname: Annotated[str, Form()],
    delivery_instructions: Annotated[str, Form()],
):
    with Session(engine) as session:
        if user := session.scalars(
            select(User).where(User.id == secretsanta_id)
        ).first():
            user.fullname = fullname
            user.delivery_instructions = delivery_instructions
            session.commit()
            return RedirectResponse("/", status_code=302)
        else:
            return HTMLResponse("User not found", status_code=404)
