import random
import secrets
import string
from typing import Annotated

from fastapi import Cookie, Depends, FastAPI, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

import h


class Base(DeclarativeBase):
    pass


def _random_string():
    return "".join(
        random.choice(string.ascii_letters + string.digits) for _ in range(6)
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(6), default=_random_string, primary_key=True)
    fullname: Mapped[str] = mapped_column(unique=True)
    delivery_instructions: Mapped[str]
    gift_recepient_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"))
    gift_recepient: Mapped["User | None"] = relationship(
        back_populates="gift_giver", remote_side=[id]
    )
    gift_giver: Mapped["User | None"] = relationship(back_populates="gift_recepient")


engine = create_engine("sqlite:///secretsanta.db")
Base.metadata.create_all(engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "kf")
    correct_password = secrets.compare_digest(credentials.password, "hools")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.get("/")
def root(
    secretsanta_id: Annotated[str | None, Cookie()] = None,
    _: str = Depends(authenticate),
):
    with Session(engine) as session:
        matchmaking_made = bool(
            session.scalars(
                select(User).where(User.gift_recepient_id.is_not(None)).limit(1)
            ).first()
        )
        if me := session.scalars(select(User).where(User.id == secretsanta_id)).first():
            return HTMLResponse(
                str(
                    h.html[
                        h.head[
                            h.title["Το λεύκωμα του Σέρβερ"],
                            h.link(rel="stylesheet", href="/static/styles.css"),
                        ],
                        h.body[
                            me.fullname == "kbairak"
                            and h.form(action="/make_matches", method="post")[
                                h.button["Create matches"]
                            ],
                            h.form(action="/logout", method="post")[
                                h.button["Log out"]
                            ],
                            not matchmaking_made
                            and h.form(action="/remove_me", method="post")[
                                h.button["Remove myself"]
                            ],
                            h.h1[f"Welcome {me.fullname}"],
                            h.p[
                                "Your ID is ",
                                h.code[me.id],
                                ", write it down in case you log out or log in from "
                                "another browser",
                            ],
                            me.gift_recepient
                            and h.fragment[
                                h.h2[
                                    "You have to buy a present for "
                                    f"{me.gift_recepient.fullname}"
                                ],
                                h.h3["Delivery instructions"],
                                h.pre[me.gift_recepient.delivery_instructions],
                            ],
                            h.h2["Change details"],
                            h.form(action="/edit_user", method="post")[
                                h.p[
                                    "Your name: ",
                                    h.input(name="fullname", value=me.fullname),
                                ],
                                h.p[
                                    "Delivery instructions: ",
                                    h.textarea(
                                        name="delivery_instructions",
                                        required="required",
                                        rows=4,
                                        cols=80,
                                    )[me.delivery_instructions],
                                ],
                                h.p[h.button["Save"]],
                            ],
                            h.h2["The participants are:"],
                            h.ul[
                                *[
                                    h.li[
                                        user.fullname,
                                        me.fullname == "kbairak"
                                        and h.fragment[
                                            " - ",
                                            user.id,
                                            h.form(
                                                action="/remove",
                                                method="post",
                                                style="display: inline",
                                            )[
                                                h.input(
                                                    type="hidden",
                                                    name="user_id",
                                                    value=user.id,
                                                ),
                                                h.button["Remove"],
                                            ],
                                        ],
                                    ]
                                    for user in session.scalars(select(User))
                                ]
                            ],
                        ],
                    ]
                )
            )
        else:
            return HTMLResponse(
                str(
                    h.html[
                        h.head[
                            h.title["Το λεύκωμα του Σέρβερ"],
                            h.link(rel="stylesheet", href="/static/styles.css"),
                        ],
                        h.body[
                            h.h3[
                                "Did you sign up from a different browser or logged "
                                "out? Log in again using your user ID:"
                            ],
                            h.form(action="/login", method="post")[
                                h.p[
                                    "User ID: ",
                                    h.input(name="id", required="required"),
                                    h.button["Log in"],
                                ]
                            ],
                            (
                                h.p["Λεύκωμα session is closed, you cannot sign up"]
                                if matchmaking_made
                                else h.fragment[
                                    h.h2["Sign up"],
                                    h.form(action="/signup", method="post")[
                                        h.p[
                                            "Your name: ",
                                            h.input(
                                                name="fullname", required="required"
                                            ),
                                        ],
                                        h.p[
                                            "Delivery instructions (address, BoxNow "
                                            "box, email, phone number): ",
                                            h.textarea(
                                                name="delivery_instructions",
                                                required="required",
                                                rows=4,
                                                cols=80,
                                            )[
                                                "Adress: \nEmail: \nPhone number: \n"
                                                "Box now locker: "
                                            ],
                                        ],
                                        h.p[h.button["Signup"]],
                                    ],
                                ]
                            ),
                        ],
                    ],
                )
            )


@app.post("/signup")
def signup(
    fullname: Annotated[str, Form()], delivery_instructions: Annotated[str, Form()]
):
    with Session(engine) as session:
        matchmaking_made = bool(
            session.scalars(
                select(User).where(User.gift_recepient_id.is_not(None)).limit(1)
            ).first()
        )
        if matchmaking_made:
            return HTMLResponse(
                "Λεύκωμα session is over, signups are closed", status_code=403
            )
        if session.scalars(select(User).where(User.fullname == fullname)).first():
            return HTMLResponse("This name already exists", status_code=409)
        session.add(
            me := User(fullname=fullname, delivery_instructions=delivery_instructions)
        )
        session.commit()
        response = RedirectResponse("/", status_code=302)
        response.set_cookie("secretsanta_id", me.id)
        return response


@app.post("/login")
def login(id: Annotated[str, Form()]):
    with Session(engine) as session:
        if me := session.scalars(select(User).where(User.id == id)).first():
            response = RedirectResponse("/", status_code=302)
            response.set_cookie("secretsanta_id", me.id)
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
                select(User).where(User.gift_recepient_id.is_not(None)).limit(1)
            ).first()
        ):
            return HTMLResponse(
                "You can't remove yourself after matchmaking has been made",
                status_code=403,
            )
        if me := session.scalars(select(User).where(User.id == secretsanta_id)).first():
            session.delete(me)
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
                select(User).where(User.gift_recepient_id.is_not(None)).limit(1)
            ).first()
        )
        if matchmaking_made:
            return HTMLResponse("Matches have already been made", status_code=403)
        if not session.scalars(
            select(User).where(User.id == secretsanta_id, User.fullname == "kbairak")
        ).first():
            return HTMLResponse("You are not allowed to make matches", status_code=403)

        users = list(session.scalars(select(User)))
        random.shuffle(users)
        for i, left in enumerate(users[:-1]):
            right = users[i + 1]
            left.gift_recepient_id = right.id
        users[-1].gift_recepient_id = users[0].id  # Last user gives gift to first
        session.commit()
        return RedirectResponse("/", status_code=302)


@app.post("/edit_user")
def edit_user(
    secretsanta_id: Annotated[str, Cookie()],
    fullname: Annotated[str, Form()],
    delivery_instructions: Annotated[str, Form()],
):
    with Session(engine) as session:
        if me := session.scalars(select(User).where(User.id == secretsanta_id)).first():
            if session.scalars(
                select(User).where(User.id != me.id, User.fullname == fullname)
            ).first():
                return HTMLResponse("This name already exists", status_code=409)
            me.fullname = fullname
            me.delivery_instructions = delivery_instructions
            session.commit()
            return RedirectResponse("/", status_code=302)
        else:
            return HTMLResponse("User not found", status_code=404)


@app.post("/remove")
def remove(secretsanta_id: Annotated[str, Cookie()], user_id: Annotated[str, Form()]):
    with Session(engine) as session:
        matchmaking_made = bool(
            session.scalars(
                select(User).where(User.gift_recepient_id.is_not(None)).limit(1)
            ).first()
        )
        if matchmaking_made:
            return HTMLResponse("Matches have already been made", status_code=403)
        if not session.scalars(
            select(User).where(User.id == secretsanta_id, User.fullname == "kbairak")
        ).first():
            return HTMLResponse("You are not allowed to remove users", status_code=403)
        if not (
            user := session.scalars(select(User).where(User.id == user_id)).first()
        ):
            return HTMLResponse("User not found", status_code=404)
        session.delete(user)
        session.commit()
    return RedirectResponse("/", status_code=302)
