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

When it's time to do the matchmaking:

```
cd /path/to/kfsecretsanta
source .venv/bin/activate
python make_matches.py
```
