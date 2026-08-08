from quiz.models import Quiz, Team

def current_quiz(request):
    # Берем последний созданный квиз для отображения названия игры в шапке
    active_quiz = Quiz.objects.last()
    
    # ПРОСТО БЕРЕМ ВСЕ КОМАНДЫ И СОРТИРУЕМ ПО ОЧКАМ
    teams_sorted = list(Team.objects.all().order_by('-score', 'name'))
        
    return {
        'CURRENT_QUIZ': active_quiz,
        'TEAM_RANKING': teams_sorted,
    }