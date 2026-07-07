from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import Team, Quiz, Block, Question, AnswerOption

def team_scores(request):
    """Главная страница — только просмотр таблицы."""
    teams = Team.objects.all().order_by('-score', 'name')
    current_quiz = Quiz.objects.last() 
    context = {'teams': teams, 'current_quiz':current_quiz}
    return render(request, 'team_scores.html', context)

def add_team_form(request):
    """Страница с чистой формой добавления команды."""
    return render(request, 'add_team.html')

def save_team(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        score = int(request.POST.get('score', 0))
        
        if not Team.objects.filter(name=name).exists():
            Team.objects.create(name=name, score=score)
        return redirect('team_scores')
    
    return redirect('add_team')

def play_block(request, block_id):
    """
    Страница игры: отображает вопросы из выбранного Блока.
    """
    block = get_object_or_404(Block, id=block_id)
    questions = block.questions.all()
    
    context = {
        'block': block,
        'questions': questions,
    }
    return render(request, 'play_block.html', context)

def save_answer(request, question_id):
    """
    Обрабатывает выбор пользователя, сверяет с правильным ответом 
    и перенаправляет дальше.
    """
    if request.method == 'POST':
        question = get_object_or_404(Question, id=question_id)
        selected_option_id = request.POST.get('answer_choice')
    
        is_correct = False
        if selected_option_id:
            try:
                option = AnswerOption.objects.get(id=selected_option_id)
                if option.is_correct:
                    is_correct = True
            except AnswerOption.DoesNotExist:
                pass # Пользователь передал несуществующий ID, считаем за ошибку
        
        next_question = question.block.questions.filter(id__gt=question.id).first()
        
        if next_question:
            # Если есть следующий вопрос — идем туда
            url = reverse('play_block', args=[question.block.id])
            
            # Добавляем параметры для отображения результата текущего вопроса
            if is_correct:
                return redirect(f'{url}?status=correct&q={question.id}')
            else:
                return redirect(f'{url}?status=wrong&q={question.id}&correct={AnswerOption.objects.filter(question=question, is_correct=True).first().id}')
        else:
            # Это был последний вопрос в блоке
            return redirect(f"{reverse('team_scores')}?block_finished={question.block.id}")
    
    # Если зашли не через POST, возвращаем назад
    return redirect('team_scores')

def edit_team(request, team_id):
    """
    Страница редактирования названия или очков конкретной команды.
    """
    team = get_object_or_404(Team, id=team_id)
    
    if request.method == 'POST':
        new_name = request.POST.get('name')
        new_score = int(request.POST.get('score', 0))
        
        team.name = new_name
        team.score = new_score
        team.save()
        
        return redirect('team_scores')
    
    context = {
        'team': team,
    }
    return render(request, 'edit_team.html', context)