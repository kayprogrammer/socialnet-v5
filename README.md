# SOCIALNET V5
A Realtime Social Networking API built with Litestar and Tortoise ORM


![alt text](https://github.com/kayprogrammer/socialnet-v5/blob/main/display/litestar.svg?raw=true)


#### LITESTAR DOCS: [Documentation](https://docs.litestar.dev/latest/)
#### TORTOISE ORM DOCS: [Documentation](https://tortoise.github.io/index.html) 
#### PG ADMIN: [Documentation](https://pgadmin.org) 


## How to run locally

* Download this repo or run: 
```bash
    $ git clone git@github.com:kayprogrammer/socialnet-V5.git
```

#### In the root directory:
- Install all dependencies
```bash
    $ pip install -r requirements.txt
```
- Create an `.env` file and copy the contents from the `.env.example` to the file and set the respective values. A postgres database can be created with PG ADMIN or psql

- Run Locally
```bash
    $ aerich init-db
```
```bash
    $ aerich mig
```
```bash
    $ litestar run --reload --debug
```

- Run With Docker
```bash
    $ docker-compose up --build -d --remove-orphans
```
OR
```bash
    $ make build
```

- Test Coverage
```bash
    $ pytest --disable-warnings -vv
```
OR
```bash
    $ make test
```

![alt text](https://github.com/kayprogrammer/socialnet-V5/blob/main/display/display1.png?raw=true)
![alt text](https://github.com/kayprogrammer/socialnet-V5/blob/main/display/display2.png?raw=true)
![alt text](https://github.com/kayprogrammer/socialnet-V5/blob/main/display/display3.png?raw=true)
![alt text](https://github.com/kayprogrammer/socialnet-V5/blob/main/display/display4.png?raw=true)
![alt text](https://github.com/kayprogrammer/socialnet-V5/blob/main/display/display5.png?raw=true)
![alt text](https://github.com/kayprogrammer/socialnet-V5/blob/main/display/display6.png?raw=true)
![alt text](https://github.com/kayprogrammer/socialnet-V5/blob/main/display/display7.png?raw=true)