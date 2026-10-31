from django.urls import path
from .views import AIChat

urlpatterns = [
    path('start/<str:agent_id>/', AIChat.as_view()),
    path('ask/<str:agent_id>/', AIChat.as_view()),
]