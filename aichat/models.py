from django.db import models

class ChatInfo(models.Model):
    user = models.CharField(max_length=20)
    answer = models.TextField()
    question = models.TextField()

    class Meta:
        db_table = 'chat_info'

    def __str__(self):
        return self.content