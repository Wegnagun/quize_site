from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages 
from .models import Team, Quiz, Block, TeamBlockResult, AnswerMark

def team_scores(request):
    """Главная страница — только просмотр таблицы."""
    teams = Team.objects.all().order_by('-score', 'name')
    current_quiz = Quiz.objects.last()
    blocks_status = {}
    for block in current_quiz.blocks.all():
        has_res = TeamBlockResult.objects.filter(block=block).exists()
        blocks_status[block.id] = has_res
    context = {
        'teams': teams, 
        'current_quiz':current_quiz, 
        'blocks_status':blocks_status
        }
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
        
        if team_result.current_question_index < questions.count() - 1:
            team_result.current_question_index += 1
            team_result.save()
            return redirect('review_team_results', block_id=block.id, team_id=team.id)
        else:
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


def check_block(request, block_id):
    """
    Страница "Судейская": сверка ответов команд по бумажке.
    """
    block = get_object_or_404(Block, id=block_id)
    teams = list(Team.objects.all().order_by('-score', 'name'))
    questions = list(block.questions.all())
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
    teams = list(Team.objects.all().order_by('-score', 'name'))
    raw_marks = request.POST.getlist('marks') 
    submitted_data = {}
    for item in raw_marks:
        try:
            t_str, q_str = item.split('_')
            t_id = int(t_str)
            q_id = int(q_str)
            submitted_data.setdefault(t_id, set()).add(q_id)
        except ValueError:
            continue

    for team in teams:
        tr, _ = TeamBlockResult.objects.get_or_create(team=team, block=block)
        correct_count = 0
        AnswerMark.objects.filter(result=tr).delete()
        
        for question in block.questions.all():
            is_correct = str(question.id) in map(str, submitted_data.get(team.id, []))
            AnswerMark.objects.create(
                result=tr,
                question=question,
                is_correct=is_correct
            )
            
            if is_correct:
                correct_count += 1
        tr.block_score = correct_count
        tr.is_finished = True
        tr.save() 
        total_from_db = sum(res.block_score for res in team.block_results.all())
        team.score = total_from_db
        team.save()

    messages.success(request, "Очки сохранены!")
    return redirect('team_scores')
