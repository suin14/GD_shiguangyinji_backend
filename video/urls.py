from django.urls import path
from .views import VideoManagement, VideoStatusView, VideoSaveView

urlpatterns = [
    path('', VideoManagement.as_view(), name='video_management'),  # 视频CRUD操作
    path('create/', VideoManagement.as_view(), name='video_create'),  # 兼容旧的create路径
    path('status/', VideoStatusView.as_view(), name='video_status'),  # 视频状态查询
    path('save/', VideoSaveView.as_view(), name='video_save'),  # 视频保存确认
]