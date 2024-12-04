# ΚΦ secret santa

## Quickstart

```sh
git clone https://github.com/kbairak/kfsecretsanta
cd kfsecretsanta
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
fastapi dev
```

> Stop the server with Ctrl-C

After the initial installation:

```sh
cd .../kfsecretsanta
source .venv/bin/activate
fastapi dev
```

In order to delete the database and start fresh:

```sh
rm secretsanta.db
```

When it's time to do the matchmaking, a button will appear only for the admin user (the one whose fullname field is "kbairak"). Pressing the button will assign matches to everyone and disable signups.

There is a corner case where an error will be raised during matchmaking. If that happens, press the button again until it succeeds.
