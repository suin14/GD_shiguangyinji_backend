from django.http import JsonResponse
from rest_framework.views import APIView
from .postrequest import send
from .models import ChatInfo
from rest_framework.permissions import IsAuthenticated, AllowAny


class AIChat(APIView):
    permission_classes = [AllowAny]
    hello = {
        'agent1': '您好啊！我是张伟，刚泡了一壶茶，正好闲下来。不知道您愿不愿意和我一起聊聊天，分享一下您的故事？我特别喜欢听别人的人生经历，总能从中学到很多。',
        'agent2': '你好！我是李娜，刚刚完成了一幅画，正准备放松一下。您愿意和我聊聊吗？我很喜欢听人们的故事和经历，这样可以让我更好地理解这个世界。',
        'agent3': '您好！我是王强，刚刚完成了一次旅行，正好有些感慨。您愿意和我分享您的故事吗？我很喜欢听人们的经历，这样可以让我更好地理解生活。',
    }

    def post(self, request, agent_id):
        q = request.POST.get('question')
        user = str(request.user)
        cid = request.POST.get('conversation_id', '')
        # print(f"Received question: {q}, user: {user}, conversation_id: {cid}")
        isOk, ret_conversation_id, ret_content, ret_status_code, ret_err_text = send(q, user,agent_id , cid)
        if isOk:
            ChatInfo.objects.create(user=user, answer=ret_content, question=q)
            return JsonResponse({'errno': 0, 'conversation_id': ret_conversation_id, 'msg': ret_content})
        else:
            return JsonResponse({'errno': 1001, 'conversation_id': ret_conversation_id, 'msg': ret_err_text})

    def get(self, request, agent_id):
        return JsonResponse({'errno': 0, 'conversation_id': '', 'msg': self.hello.get(agent_id)})
