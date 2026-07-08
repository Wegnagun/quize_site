from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Team, Quiz, Block, Question


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Отображение команд в админке."""
    list_display = ['name', 'score']
    verbose_name = 'Команда'
    verbose_name_plural = 'Команды'


class QuestionInline(admin.TabularInline):
    """Вывод вопросов внутри страницы блока."""
    model = Question
    extra = 1
    fields = ('text', 'answer')
    verbose_name = "Вопрос"
    verbose_name_plural = "Вопросы раунда"


class BlockInline(admin.TabularInline):
    """Вывод блоков внутри страницы самого квиза."""
    model = Block
    extra = 1
    inlines = [QuestionInline]
    fields = ('title', 'order')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    """Отображение квизов в админке."""
    list_display = ('title',)
    search_fields = ('title',)
    inlines = [BlockInline]


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ('title', 'quiz', 'order')
    list_filter = ('quiz',)
    ordering = ('quiz__title', 'order')
    search_fields = ('title', 'quiz__title')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'block', 'answer_preview')
    list_filter = ('block__quiz', 'block')
    search_fields = ('text', 'answer')
    autocomplete_fields = ['block']
    
    def answer_preview(self, obj):
        """Обрезаем длинный ответ, чтобы таблица была аккуратной"""
        if obj.answer:
            return obj.answer[:40] + ("..." if len(obj.answer) > 40 else "")
        return "-"
    answer_preview.short_description = 'Ответ'


admin.site.unregister(Group)
