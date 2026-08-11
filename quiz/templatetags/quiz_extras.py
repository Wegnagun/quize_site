from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def find(queryset, lookup_value):
    """Находит объект в QuerySet по полю"""
    # queryset здесь - это marks (AnswerMark)
    # Но так как мы передаем вопрос, ищем просто наличие связи
    # Упрощенная логика: если есть хоть одна отметка на этот вопрос для этой команды
    # В идеале лучше передавать готовый словарь {team_id: {question_id: True/False}}
    pass 