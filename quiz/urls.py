from django.urls import path
from .views import (team_scores, add_team_form, save_team, 
                    play_block, edit_team, check_block, save_marks, review_team_results_next)

urlpatterns = [
    path('', team_scores, name='team_scores'),
    path('add/', add_team_form, name='add_team'),
    path('save/', save_team, name='save_team'),
    path('block/<int:block_id>/', play_block, name='play_block'),
    path('edit/<int:team_id>/', edit_team, name='edit_team'),
    path('check/<int:block_id>/', check_block, name='check_block'),
    path('check/<int:block_id>/save/', save_marks, name='save_marks'),
    path('results/next/<int:block_id>/<int:team_id>/', review_team_results_next, name='review_team_results_next'),
]
