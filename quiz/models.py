from django.db import models


class Team(models.Model):
    """Модель Команд."""
    
    name = models.CharField(
        max_length=250,
        unique=True,
        verbose_name='Наименование команды',
        help_text='Наименование команды'
    )
    score = models.IntegerField(
        default=0, 
        verbose_name='Набранные очки',
        help_text='Набранные очки'
        )

    class Meta:
        verbose_name = 'Команда'
        verbose_name_plural = 'Команды'
        ordering = ('-score', 'name') 


class Quiz(models.Model):
    """Контейнер для набора блоков."""
    title = models.CharField(
        max_length=250,
        unique=True,
        verbose_name='Название квиза',
        help_text='Например: Вечерний квиз 7 июля'
    )
    
    class Meta:
        verbose_name = 'Квиз'
        verbose_name_plural = 'Квизы'
        
    def __str__(self):
        return self.title


class Block(models.Model):
    """
    Тематический блок вопросов (раунд).
    Напрямую привязан к конкретному квизу.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='blocks')
    title = models.CharField(max_length=250, verbose_name='Название блока/темы')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок вывода')

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Блок вопросов'
        verbose_name_plural = 'Блоки вопросов'
        
    def __str__(self):
        return f"{self.quiz.title} — {self.title}"



class Question(models.Model):
    """Конкретный вопрос внутри тематического блока."""
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField(verbose_name="Текст вопроса")
    answer = models.CharField(
        max_length=500, 
        verbose_name="Правильный ответ", 
        blank=True, 
        help_text="Для ведущего: правильный вариант"
    )
    
    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        
    def __str__(self):
        return f"Вопрос: {self.text[:60]}"


class TeamBlockResult(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='block_results')
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='team_results')
    current_question_index = models.PositiveIntegerField(default=0, verbose_name='Текущий вопрос') 
    is_finished = models.BooleanField(default=False, verbose_name='Раунд проверен')
    checked_at = models.DateTimeField(null=True, blank=True, verbose_name='Время проверки')

    class Meta:
        unique_together = ('team', 'block')
        verbose_name = 'Результат команды в раунде'
        verbose_name_plural = 'Результаты команд в раундах'
        
    @property
    def correct_count(self):
        """Свойство: считаем количество правильных ответов"""
        return self.marks.filter(is_correct=True).count()
        
    @property
    def total_points(self):
        """Свойство: итоговые баллы за раунд (стандарт 1 балл за вопрос)"""
        return self.correct_count 
    
    @property
    def progress(self):
        total = self.block.questions.count()
        if total == 0: return "0/0"
        return f"{self.current_question_index}/{total}"
        
    def __str__(self):
        status = "Проверено" if self.is_finished else "В процессе"
        return f"{self.team.name} | {self.block.title} ({status})"


class AnswerMark(models.Model):
    result = models.ForeignKey(TeamBlockResult, on_delete=models.CASCADE, related_name='marks')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_correct = models.BooleanField(default=False, verbose_name='Ответ верный')

    class Meta:
        unique_together = ('result', 'question')
        verbose_name = "Отметка ответа"
        verbose_name_plural = "Отметки ответов"
        
    def __str__(self):
        mark = "✅" if self.is_correct else "❌"
        return f"{mark} Вопрос {self.question.id} для {self.result.team.name}"
    