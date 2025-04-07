# ctbus_finance

A simple finance tracker using Python, SQLite, and Yahoo Finance

## Usage

Go through and add your accounts:

```
ctbus_finance create_account "Account 1" Cash
ctbus_finance create_account "Account 2" "Roth IRA"
```



## Dev

### Database migration

After making updates to the database models, you can update your schema using alembic:

```
alembic init alembic
(Go into alembic.ini and modify sqlalchemy.url to point to your database)
(Go into alembic/env.py and replace `target_metadata = None` with `from ctbus_finance import models` and `target_metadata = models.Base.metadata`)
alembic -c alembic.ini revision --autogenerate -m "Description of changes"
(Review script in alembic/versions/new_script_name.py)
alembic upgrade head
```