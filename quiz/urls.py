from django.urls import path
from .views import (team_scores, add_team_form, save_team, 
                    play_block, edit_team, check_block, save_marks, review_team_results_next, check_block)

urlpatterns = [
    path('', team_scores, name='team_scores'),
    path('add/', add_team_form, name='add_team'),
    path('save/', save_team, name='save_team'),
    path('block/<int:block_id>/', play_block, name='play_block'),
    path('edit/<int:team_id>/', edit_team, name='edit_team'),
    path('results/next/<int:block_id>/<int:team_id>/', review_team_results_next, name='review_team_results_next'),
    path('check/<int:block_id>/', check_block, name='check_block'),
    path('save_marks/<int:block_id>/', save_marks, name='save_marks'),
]
