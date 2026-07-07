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
    
    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        
    def __str__(self):
        return f"Вопрос: {self.text[:60]}"


class AnswerOption(models.Model):
    """Вариант ответа на вопрос."""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255, verbose_name="Вариант ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный ответ")
    
    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответов"
        
    def __str__(self):
        status = " (Верно)" if self.is_correct else ""
        return f"{self.text}{status}"