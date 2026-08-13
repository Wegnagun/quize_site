from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth.models import Group
from django.db.models import Sum, F
from .models import Team, Quiz, Block, Question, AnswerMark, TeamBlockResult


class AnswerMarkInline(admin.TabularInline):
    """Отметки о правильности ответов ВНУТРИ вопроса."""
    model = AnswerMark
    extra = 0  # Не показываем пустые строки по умолчанию
    fields = ('question', 'is_correct')
    readonly_fields = ('question',) # Вопрос нельзя менять из формы отметки
    verbose_name = "Ответ"
    verbose_name_plural = "Ответы команд"
    
    def has_add_permission(self, request, obj=None):
        return False # Добавляем только через автоматический подсчет
    

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Отображение команд в админке."""
    list_display = ['name', 'score']
    ordering = ('-score', 'name')
    actions = ['zero_out_scores']
    verbose_name = 'Команда'
    verbose_name_plural = 'Команды'

    @admin.action(description="Обнулить очки выбранным командам")
    def zero_out_scores(self, request, queryset):
        teams_to_update = queryset.order_by()    
        teams_to_update.update(score=0,)
        
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            total_score=Sum('block_results__marks__is_correct')
        ).order_by('-total_score')



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


class TeamBlockResultInline(admin.TabularInline):
    """Результаты команд ВНУТРИ блока в админке (для быстрой правки)."""
    model = TeamBlockResult
    extra = 0
    fields = ('team', 'score', 'is_finished', 'checked_at')
    readonly_fields = ('checked_at',)
    verbose_name = "Результат команды"
    verbose_name_plural = "Результаты команд"


@admin.register(TeamBlockResult)
class TeamBlockResultAdmin(admin.ModelAdmin):
    list_display = ('team_link', 'block_title', 'correct_count', 'total_points', 'status_badge', 'checked_at')
    list_filter = ('block__quiz', 'block', 'is_finished')
    search_fields = ('team__name', 'block__title')
    date_hierarchy = 'checked_at'
    actions = ['mark_as_checked', 'reset_team_block_result']
    list_per_page = 25

    def team_link(self, obj):
        from django.urls import reverse
        url = reverse("admin:quiz_team_change", args=[obj.team.id])
        return format_html('<a href="{}" target="_blank">{}</a>', url, obj.team.name)
    team_link.admin_order_field = 'team__name'
    team_link.short_description = 'Команда'

    def block_title(self, obj):
        return obj.block.title
    block_title.admin_order_field = 'block__title'
    block_title.short_description = 'Раунд/Блок'

    def status_badge(self, obj):
        if obj.is_finished:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', '✅ Проверено')
        return format_html('<span style="color: orange;">{}</span>', 'В процессе')

    def mark_as_checked(self, request, queryset):
        updated = queryset.update(is_finished=True)
        self.message_user(request, f"Отмечено как проверенные: {updated}")
    mark_as_checked.short_description = "Отметить выбранные как «Проверено»"

    def reset_team_block_result(self, request, queryset):
        for res in queryset:
            # Удаляем все галочки (AnswerMarks)
            res.marks.all().delete()
            # Сбрасываем счетчик вопросов и статус
            res.current_question_index = 0
            res.is_finished = False
            res.save()
        self.message_user(request, "Очки сброшены до 0, прогресс очищен.")
    reset_team_block_result.short_description = "Сбросить результаты выбранной команды в раунде"

admin.site.unregister(Group)
