from django.urls import path
from .views import CharacterView, UserCharacterView

urlpatterns = [
    path("characters/", CharacterView.as_view(), name="character-list"),
    path(
        "characters/<int:character_id>/",
        CharacterView.as_view(),
        name="character-detail",
    ),
    path("characters/search/", CharacterView.as_view(), name="character-search"),
    path("user-character/", UserCharacterView.as_view(), name="user-character"),
]
