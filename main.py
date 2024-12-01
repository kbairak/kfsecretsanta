from typing import Annotated

from fastapi import Cookie, FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from engine import User, engine
from h import button, code, form, fragment, h1, h2, h3, input, li, p, textarea, ul

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
                                p[user.gift_recepient.delivery_instructions],
                            ]
                            if user.gift_recepient_id
                            else []
                        ),
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
                                    name="delivery_instructions", required="required"
                                )[""],
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
