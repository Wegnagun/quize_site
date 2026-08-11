from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages 
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
    questions = list(block.questions.all().order_by('id'))
    context = {
        'quiz_block': block,
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


from django.shortcuts import render, get_object_or_404

# quiz/views.py

def check_block(request, block_id):
    """
    Страница "Судейская": сверка ответов команд по бумажке.
    """
    block = get_object_or_404(Block, id=block_id)
    
    # Получаем все объекты одним запросом к БД
    teams = list(Team.objects.all().order_by('-score', 'name'))
    questions = list(block.questions.all())
    
    # Собираем ВСЕ метки за этот блок в один словарь {team_id: {question_id: AnswerMark}}
    marks_map = {}
    all_marks = AnswerMark.objects.filter(
        result__block=block,
        question__in=questions
    ).select_related('result__team', 'question')
    
    for mark in all_marks:
        t_id = mark.result.team.id
        q_id = mark.question.id
        
        if t_id not in marks_map:
            marks_map[t_id] = {}
        marks_map[t_id][q_id] = mark

    context = {
        'quiz_block': block,
        'teams': teams,
        'questions': questions,
        'marks_map': marks_map,
    }
    return render(request, 'check_block.html', context)


def save_marks(request, block_id):
    if request.method != 'POST':
        return redirect('team_scores')
        
    block = get_object_or_404(Block, id=block_id)
    
    # Собираем данные из формы: { team_id: [list_of_question_ids] }
    submitted_data = {}
    for key in request.POST.keys():
        if not key.startswith('mark_'):
            continue
        try:
            _, t_id_str, q_id_str = key.split('_')
            t_id, q_id = int(t_id_str), int(q_id_str)
            submitted_data.setdefault(t_id, set()).add(q_id)
        except (ValueError, IndexError):
            continue

    teams = Team.objects.all().order_by('-score', 'name')

    # Проходим циклом ПО ВСЕМ командам раунда для полного обновления состояния
    for team in teams:
        # Получаем результат этой команды в этом блоке
        team_result, created = TeamBlockResult.objects.get_or_create(
            team=team,
            block=block
        )
        
        # 1. Стираем все старые отметки этого блока для этой команды
        team_result.marks.all().delete()
        
        correct_count = 0
        
        # 2. Проходим по всем вопросам блока
        for question in block.questions.all():
            
            # Проверяем, была ли галочка установлена пользователем
            is_checked_in_form = (
                str(team.id) + "_" + str(question.id) in [
                    f"{t}_{q}" for tid, qs in submitted_data.items() for q in qs
                ]
            )
            
            # Создаем метку (AnswerMark)
            AnswerMark.objects.create(
                result=team_result,
                question=question,
                is_correct=is_checked_in_form
            )
            
            if is_checked_in_form:
                correct_count += 1

        # --- КРИТИЧЕСКИ ВАЖНЫЙ БЛОК ---
        # Пересчитываем ОБЩИЙ счет команды СУММАРНО за все раунды
        total_score = sum(res.total_points for res in team.block_results.all())
        team.score = total_score
        team.save() # Сохраняем изменение очков ВНЕШНЕЙ модели Team
        
        # Обновляем статус текущей проверки
        team_result.is_finished = True
        team_result.checked_at = timezone.now()
        team_result.save() 
        # Обратите внимание: мы НЕ пишем в team_result.correct_count!

    messages.success(request, f"Результаты блока «{block.title}» успешно сохранены.")
    return redirect('team_scores')
