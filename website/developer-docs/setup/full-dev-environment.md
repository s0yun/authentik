---
title: Full development environment
---

## Requirements

-   Python 3.10
-   poetry, which is used to manage dependencies, and can be installed with `pip install poetry`
-   Go 1.18
-   PostgreSQL (any recent version will do)
-   Redis (any recent version will do)
-   Node 16 (or later)

## Services Setup

For PostgreSQL and Redis, you can use the docker-compose file in `scripts/`.  
You can also use a native install, if you prefer.

## Backend Setup

```shell
poetry shell # Creates a python virtualenv, and activates it in a new shell
poetry install # Install all required dependencies, including development dependencies
```

To configure authentik to use the local databases, create a file in the authentik directory called `local.env.yml`, with the following contents

```yaml
debug: true
postgresql:
    user: postgres

log_level: debug
secret_key: "A long key you can generate with `pwgen 40 1` for example"
```

To apply database migrations, run `make migrate`. This is needed after the initial setup, and whenever you fetch new source from upstream.

Generally speaking, authentik is a Django application, ran by gunicorn, proxied by a Go application. The Go application serves static files.

Most functions and classes have type-hints and docstrings, so it is recommended to install a Python Type-checking Extension in your IDE to navigate around the code.

Before committing code, run `make lint` to ensure your code is formatted well. This also requires `pyright@1.1.136`, which can be installed with npm.

Run `make gen` to generate an updated OpenAPI document for any changes you made.

## Frontend Setup

By default, no compiled bundle of the frontend is included so this step is required even if you're not developing for the UI.

To build the UI once, run `web-build`.

Alternatively, if you want to live-edit the UI, you can run `make web-watch` instead.  
This will immediately update the UI with any changes you make so you can see the results in real time without needing to rebuild.

To format the frontend code, run `make web`.

## Running

Now that the backend and frontend have been setup and built, you can start authentik by running `make run`. authentik should now be accessible at `http://localhost:9000`.
