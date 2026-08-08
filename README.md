python -m venv venv
source venv/bin/activate
pip freeze > requirements.txt
python manage.py runserver