from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Team, Quiz, Block, Question, AnswerOption


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Отображение команд в админке."""
    list_display = ['name', 'score']
    verbose_name = 'Команда'
    verbose_name_plural = 'Команды'


class AnswerOptionInline(admin.TabularInline):
    """Вывод вариантов ответа внутри страницы вопроса."""
    model = AnswerOption
    extra = 1  # Количество пустых полей для новых ответов при открытии формы
    min_num = 1
    max_num = 6
    verbose_name = "Вариант"
    verbose_name_plural = "Варианты ответов"


class QuestionInline(admin.TabularInline):
    """Вывод вопросов внутри страницы блока."""
    model = Question
    extra = 1
    inlines = [AnswerOptionInline]  # Вложенность: в вопросе сразу видны ответы
    
    def has_change_permission(self, request, obj=None):
        return True

    def has_add_permission(self, request, obj=None):
        return True


class BlockInline(admin.TabularInline):
    """Вывод блоков внутри страницы самого квиза."""
    model = Block
    extra = 1
    inlines = [QuestionInline]  # Вложенность: в блоке сразу видны вопросы
    
    # Чтобы порядок 'order' было удобно менять перетаскиванием,
    # можно подключить библиотеку sortableinline.js, но пока оставим так.
    fields = ('title', 'order')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Отображение квизов в админке."""
    list_display = ('title',)
    search_fields = ('title',)
    inlines = [BlockInline]


# Регистрация оставшихся моделей нужна только если вы хотите видеть их 
# отдельными пунктами в меню слева (для быстрого поиска или удаления).
# Если управление идет ТОЛЬКО через страницу Quiz, эти строки можно удалить.
@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('title', 'quiz', 'order')
    list_filter = ('quiz',)
    ordering = ('quiz__title', 'order')
    search_fields = ('title', 'quiz__title')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'block')
    list_filter = ('block__quiz', 'block')
    search_fields = ('text',)
    autocomplete_fields = ['block']


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__block__quiz')
    search_fields = ('text', 'question__text')

admin.site.unregister(Group)
