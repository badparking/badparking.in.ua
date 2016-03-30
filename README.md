# badparking.in.ua
New version of badparking.in.ua. Now with mobile apps.

# Local installation
* Install python 3.5 and postgresql.
* Install virtualenv
* Clone repository
* Create virtualenv outside of repo: `virtualenv venv`
* Activate virtualenv: `source venv/bin/activate`
* Install requirements: `pip install -r badparking.in.ua/requirements.txt`
* Create db user: `createuser badparking_user`
* Create db: `createdb badparking_db -Obadparking_user`
* Create `local_settings.py` next to `settings.py`
* Add following settings there:
```python
ALLOWED_HOSTS = ["*"]
DEBUG = True

DATABASES = {
    'default': {
        # Strictly PostgreSQL
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'badparking_db',
        'USER': 'badparking_user',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```
* Run `./manage.py migrate` to create/populate db tables
* Run `./manage.py createsuperuser` to create account for superuser
* Run `./manage.py runserver`
* Open http://127.0.0.1:8000 in your browser.
