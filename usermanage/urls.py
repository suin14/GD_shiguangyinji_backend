from django.urls import path
from .views import RegisterView, CheckUsernameExistView, CheckPhoneExistView, LoginView, CheckLoginStatusView, \
    VerifyTokenView, LogoutView, GetUserProfileView, EditUserProfileView, GetUserAvatarView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('check-username/', CheckUsernameExistView.as_view(), name='check-username-exist'),
    path('check-phone/', CheckPhoneExistView.as_view(), name='check-phone-exist'),
    path('login/', LoginView.as_view(), name='login'),
    path('check-login/', CheckLoginStatusView.as_view(), name='check-login'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("get-profile/", GetUserProfileView.as_view(), name="get_profile"),
    path('edit-profile/', EditUserProfileView.as_view(), name='edit-profile'),
    path('get-avatar/', GetUserAvatarView.as_view(), name='get_user_avatar'),
]
