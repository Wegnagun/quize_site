from django.contrib import admin
from django.contrib.auth.models import Group
from .models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Отображение команд в админке"""
    list_display = ['name', 'score']
    verbose_name = 'Команда'
    verbose_name_plural = 'Команды'

admin.site.unregister(Group)
