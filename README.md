# badparking.in.ua
New version of badparking.in.ua. Now with mobile apps.

# Local installation
1. Install python 3.5 and postgresql.
2. Install virtualenv
3. Clone repository
4. Create virtualenv outside of repo: `virtualenv venv`
5. Activate virtualenv: `source venv/bin/activate`
6. Install requirements: `pip install -r badparking.in.ua/requirements.txt`
7. Create db user: `createuser badparking_user`
8. Create db: `createdb badparking_db -Obadparking_user`
9. Create `local_settings.py` next to `settings.py`
10. Add following settings there:
11. Run `./manage.py migrate`
12. Run `./manage.py runserver`
