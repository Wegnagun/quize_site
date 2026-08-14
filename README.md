python -m venv venv
source venv/bin/activate
pip freeze > requirements.txt
python manage.py runserver


загрузка вопросов
python manage.py load_questions --quiz-id {айди квиза} --block-title {наименование блока где будут все вопросы, по умолчанию "Все вопросы"} --path {путь к файлу по умолчанию 'quiz/data/questions.json'}

Пример: python manage.py load_questions --quiz-id 1

создание раундов
python manage.py generate_rounds --quiz-id {айди квиза} --questions-per-round {количество вопросов в раунде}

Пример: python manage.py generate_rounds --quiz-id 1 --questions-per-round 8



