import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from quiz.models import Question, Block, Quiz

class Command(BaseCommand):
    help = 'Загружает вопросы викторины из JSON-файла'

    def add_arguments(self, parser):
        # Указываем ID Квиза (Quiz), к которому привяжутся блоки и вопросы
        parser.add_argument(
            '--quiz-id',
            type=int,
            required=True,
            help='ID объекта Quiz, для которого загружаются данные'
        )
        parser.add_argument(
            '--block-title',
            type=str,
            default='Общие вопросы',
            help='Название блока (поле title), куда будут добавлены вопросы'
        )
        parser.add_argument(
            '--path',
            type=str,
            default='quiz/data/questions.json',
            help='Путь к JSON-файлу относительно корня проекта'
        )

    def handle(self, *args, **options):
        quiz_id = options['quiz_id']
        block_title = options['block_title']
        file_path = options['path']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise CommandError(f'Файл {file_path} не найден.')
        except json.JSONDecodeError:
            raise CommandError('Ошибка декодирования JSON.')

        # 1. Находим целевой Квиз
        try:
            target_quiz = Quiz.objects.get(id=quiz_id)
        except Quiz.DoesNotExist:
            raise CommandError(f'Квиз с ID={quiz_id} не найден. Создайте квиз перед импортом вопросов.')

        # 2. Ищем или создаем Блок внутри этого Квиза
        target_block, created = Block.objects.get_or_create(
            quiz=target_quiz,
            title=block_title
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Создан новый блок: "{target_block.title}"'))
        else:
            self.stdout.write(self.style.NOTICE(f'Используется существующий блок: "{target_block.title}"'))

        # 3. Загрузка вопросов
        added_count = 0
        skipped_count = 0

        for item in data:
            # Проверяем наличие вопроса именно в этом блоке по тексту
            obj, text_created = Question.objects.get_or_create(
                block=target_block,
                text=item['question'],
                defaults={'answer': item['answer']}
            )
            
            if text_created:
                added_count += 1
            else:
                # Если вопрос уже есть, обновим ответ на актуальный (на случай опечаток в файле)
                if obj.answer != item['answer']:
                    obj.answer = item['answer']
                    obj.save()
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Импорт завершен.\n'
                f'Блок: "{target_block.title}" (ID: {target_block.id})\n'
                f'Добавлено новых вопросов: {added_count}\n'
                f'Обновлено ответов / пропущено дублей: {skipped_count}'
            )
        )