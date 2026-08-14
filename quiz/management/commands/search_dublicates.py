from django.core.management.base import BaseCommand
from quiz.models import Block, Question


class Command(BaseCommand):
    help = 'Поиск дублей вопросов: внутри блоков и между разными блоками.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Аудит базы данных: Поиск дублей ==="))

        blocks = Block.objects.exclude(id=5)
        all_questions = list(Question.objects.filter(block__in=blocks).values('id', 'text', 'block_id'))
        dublicates = []
        for i in all_questions:
            if all_questions.count(i) >= 2:
                dublicates.append(i)
                print(f'Дублика {i}')
