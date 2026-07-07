from django.urls import path
from .views import team_scores, add_team_form, save_team

urlpatterns = [
    path('', team_scores, name='team_scores'),
    path('add/', add_team_form, name='add_team'),
    path('save/', save_team, name='save_team'),
]
