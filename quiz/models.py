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
        ordering = ('name',)