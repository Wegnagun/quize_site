import random
from django.core.management.base import BaseCommand
from django.db import transaction
from quiz.models import Quiz, Block, Question
import math

class Command(BaseCommand):
    help = 'Генерирует тематические блоки (раунды) из общего пула вопросов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quiz-id',
            type=int,
            required=True,
            help='ID квиза, для которого нужно сгенерировать раунды.'
        )
        
        parser.add_argument(
            '--questions-per-round',
            type=int,
            default=10,
            help='Количество вопросов в каждом раунде.'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        quiz_id = options['quiz_id']
        questions_per_round = options['questions_per_round']

        try:
            quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Квиз с ID {quiz_id} не найден!'))
            return

        all_questions = list(Question.objects.filter(block__quiz=quiz))
        rounds_count = math.ceil(len(all_questions)/questions_per_round)
        
        if not all_questions:
            self.stdout.write(self.style.WARNING('В этом квизе нет вопросов.'))
            return
        
        self.stdout.write(f"Создаем {rounds_count} раундов по {questions_per_round} вопросов...")
        random.shuffle(all_questions)
        created_blocks = []
        
        for i in range(rounds_count):
            block_title = f"{i + 1} раунд"
            block_obj, created = Block.objects.get_or_create(
                quiz=quiz,
                title=block_title,
                defaults={'order': i}
            )
            
            if not created:
                Question.objects.filter(block=block_obj).delete()
                self.stdout.write(f"Раунд '{block_title}' перезаписывается.")
            
            created_blocks.append(block_obj)
            start_index = i * questions_per_round
            end_index = start_index + questions_per_round
            round_questions = all_questions[start_index:end_index]
            
            for question_data in round_questions:
                question = Question(
                    block=block_obj,
                    text=question_data.text,
                    answer=question_data.answer
                )
                question.save()
            self.stdout.write(self.style.SUCCESS(f"Создан блок '{block_obj.title}' ({len(round_questions)} вопросов)"))
        self.stdout.write(self.style.SUCCESS(f"\n✅ Готово! Создано/обновлено {len(created_blocks)} раундов."))
