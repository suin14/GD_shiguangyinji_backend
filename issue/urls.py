from django.urls import path
from .views import *

urlpatterns = [
    path('issue/0/', IssueManagement.as_view(who=0), name='my_issue'),
    path('issue/1/', IssueManagement.as_view(who=1), name='others_issue'),
    path('search/', IssueSearch.as_view(), name='issue_search'),
    path('create/', IssueCreate.as_view(), name='issue_create'),
    path('picture/', PictureManagement.as_view(), name='picture_management'),
    path('expand-text/', TextExpandView.as_view(), name='text_expand'),
    path('image-proxy/', ImageProxyView.as_view(), name='image_proxy'),
]