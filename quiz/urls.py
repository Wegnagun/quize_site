from django.urls import path
from .views import team_scores, add_team_form, save_team, play_block, save_answer, edit_team

urlpatterns = [
    path('', team_scores, name='team_scores'),
    path('add/', add_team_form, name='add_team'),
    path('save/', save_team, name='save_team'),
    path('block/<int:block_id>/', play_block, name='play_block'),
    path('answer/<int:question_id>/', save_answer, name='save_answer'),
    path('edit/<int:team_id>/', edit_team, name='edit_team'),
]
