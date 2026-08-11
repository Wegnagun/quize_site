from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .models import Team, Quiz, Block, Question, TeamBlockResult, AnswerMark

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
    questions = block.questions.all().order_by('id')
     # ДОБАВЬТЕ ЭТУ СТРОКУ:
    print("--- DEBUG BLOCK OBJECT ---")
    print(block.id)           # Покажет строковое представление __str__
    print(block.title)     # Покажет ВСЕ поля как словарь {'id': 1, 'title': '...', ...}

    
    context = {
        'block': block,
        'questions': questions,
    }
    return render(request, 'play_block.html', context)

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


def review_team_results(request, block_id, team_id):
    """
    Страница построчной проверки ответов команды в конкретном раунде.
    """
    block = get_object_or_404(Block, id=block_id)
    team = get_object_or_404(Team, id=team_id)
    
    team_result, created = TeamBlockResult.objects.get_or_create(team=team, block=block)
    questions = block.questions.all().order_by('id')
    
    if not questions.exists():
        team_result.is_finished = True
        team_result.save()
        return redirect('review_team_results_next', block_id=block.id, team_id=team.id)

    if request.method == 'POST' and 'question_id' in request.POST:
        q_id = int(request.POST['question_id'])
        is_correct = f'q_{q_id}' in request.POST
        
        AnswerMark.objects.update_or_create(
            result=team_result,
            question_id=q_id,
            defaults={'is_correct': is_correct}
        )
        
        # Переключаем на следующий вопрос
        if team_result.current_question_index < questions.count() - 1:
            team_result.current_question_index += 1
            team_result.save()
            return redirect('review_team_results', block_id=block.id, team_id=team.id)
        else:
            # Вопросы закончились, помечаем как завершенное
            team_result.is_finished = True
            team_result.checked_at = timezone.now()
            team_result.save()
            return redirect('review_team_results_next', block_id=block.id, team_id=team.id)
            
    try:
        current_question = questions[team_result.current_question_index]
    except IndexError:
        current_question = None

    context = {
        'block': block,
        'team': team,
        'team_result': team_result,
        'current_question': current_question,
        'all_questions': questions,
    }
    return render(request, 'review_team.html', context)


def review_team_results_next(request):
    """Главная страница — таблица лидеров с прогрессом раундов."""
    teams = Team.objects.all().order_by('-score', 'name')
    quiz = Quiz.objects.last()
    
    first_block = None
    if quiz:
        first_block = quiz.blocks.filter(questions__isnull=False).first()

    # Если первый раунд существует, готовим флаги прогресса
    if first_block:
        for team in teams:
            # Ищем существующую запись О ПРОВЕРКЕ этой команды в этом раунде
            existing_res = TeamBlockResult.objects.filter(team=team, block=first_block).first()
            
            if existing_res and existing_res.is_finished:
                team.round_1_done = True
                
                next_b = quiz.blocks.filter(id__gt=first_block.id).order_by('id').first()
                team.next_block = next_b
                team.has_next = bool(next_b)
            else:
                team.round_1_done = False
                team.next_block = None
                team.has_next = False
                
    context = {
        'teams': teams,
        'quiz': quiz,
        'first_block': first_block,
    }
    return render(request, 'team_scores.html', context)


def check_block(request, block_id):
    """
    Страница "Судейская": сверка ответов команд по бумажке.
    """
    block = get_object_or_404(Block, id=block_id)
    questions = block.questions.all().order_by('id')
    teams = Team.objects.all().order_by('-score', 'name')
    
    # Собираем текущие результаты, чтобы чекбоксы были отмечены при открытии
    team_results = {}
    for team in teams:
        result, created = TeamBlockResult.objects.get_or_create(team=team, block=block)  # шо нах за креатед?????
        team_results[team.id] = result
        
    context = {
        'block': block,
        'questions': questions,
        'teams': teams,
        'team_results': team_results,
    }
    return render(request, 'check_block.html', context)


def save_marks(request, block_id):
    if request.method == 'POST':
        block = get_object_or_404(Block, id=block_id)
        
        # Определяем, какую команду мы только что проверили
        team_id = int(request.POST.get('team_id'))
        team = get_object_or_404(Team, id=team_id)
        
        team_result, _ = TeamBlockResult.objects.get_or_create(team=team, block=block)
        
        questions = list(block.questions.all())
        correct_count = 0

        for question in questions:
            checkbox_name = f'mark_{team.id}_{question.id}'
            is_correct = checkbox_name in request.POST
            
            AnswerMark.objects.update_or_create(
                result=team_result,
                question=question,
                defaults={'is_correct': is_correct}
            )
            if is_correct:
                correct_count += 1

        # Пересчет общего счета команды
        total_score = sum(res.total_points for res in team.block_results.all())
        team.score = total_score
        team.save()
        
        team_result.is_finished = True
        team_result.checked_at = timezone.now()
        team_result.save()

        # --- ЛОГИКА ПЕРЕХОДА ---
        all_teams = list(Team.objects.all().order_by('-score', 'name'))
        
        try:
            current_index = [t.id for t in all_teams].index(team.id)
            next_team = None
            
            # Ищем следующую НЕПРОВЕРЕННУЮ команду в ЭТОМ же раунде
            for i in range(current_index + 1, len(all_teams)):
                candidate = all_teams[i]
                cand_res, _ = TeamBlockResult.objects.get_or_create(team=candidate, block=block)
                if not cand_res.is_finished:
                    next_team = candidate
                    break
            
            if next_team:
                # Если нашли — ведем к ней на ту же страницу check_block
                return redirect('check_block', block_id=block.id) + f'?team={next_team.id}'
            else:
                # Если эта команда была последней в раунде -> ищем СЛЕДУЮЩИЙ БЛОК
                next_block = Block.objects.filter(id__gt=block.id).order_by('id').first()
                
                if next_block:
                    first_team = all_teams[0]
                    nb_res, _ = TeamBlockResult.objects.get_or_create(team=first_team, block=next_block)
                    if not nb_res.is_finished:
                        return redirect('check_block', block_id=next_block.id) + '?team=' + str(first_team.id)
                
                # Если раунды кончились вообще
                messages.success(request, "Все раунды завершены!")
                return redirect('team_scores')

        except ValueError:
             return redirect('team_scores')

    return redirect('team_scores')
