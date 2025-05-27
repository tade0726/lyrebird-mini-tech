# Lyrebird Mini Tech


## How to setup


I have created a Makefile to help you setup the environment with commands.

### Prepare python environment

1. install uv

https://docs.astral.sh/uv/getting-started/installation/

2. create virtual environment


https://docs.astral.sh/uv/pip/environments/


### Prepare .env file
1. copy .env.example to .env, use this template to fill in the .env file


### Prepare database

1. start docker

```bash
make start-service
```

2. init db with alembic
```bash
make init-db
```


### Start the dev server
```bash
make dev-fastapi
```


## TODO

- [x] docker
- [x] database ORM
- [x] prompts
- [x] service
- [x] fix preference logic, need an edit obj creation then preferences creation
    -  [x] create user edit
    -  [x] create user preferences
- [ ] env frame work
- [ ] frontend

