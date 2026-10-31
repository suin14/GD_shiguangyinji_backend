import requests
from django.conf import settings

personal_access_token = settings.SECRETS['personal_access_token']

post_url = 'https://api.coze.cn/open_api/v2/chat'

headers = {
    'Authorization': f'Bearer {personal_access_token}',
    'Content-Type': 'application/json',
    'Accept': '*/*',
    'Connection': 'keep-alive'
}

payload_base = {
    'stream': False
}

def send(query, user, agent_id, conversation_id=''):
    post_payload = payload_base.copy()  # 避免全局污染

    if conversation_id != '':
        post_payload['conversation_id'] = conversation_id
    
    bot_id = settings.SECRETS.get(agent_id, 'agent1')
    post_payload['bot_id'] = bot_id
    post_payload['query'] = query
    post_payload['user'] = user
    print('post_payload:', post_payload)
    post_response = requests.post(post_url, headers=headers, json=post_payload)
    post_response_data = post_response.json()
    print(f"Response data: {post_response_data}")

    if post_response_data.get('code') == 0:
        isOk = True
        ret_conversation_id = post_response_data['conversation_id']
        ret_content = post_response_data['messages'][0]['content']
        ret_status_code = ''
        ret_err_text = ''
    else:
        isOk = False
        ret_conversation_id = ''
        ret_content = ''
        ret_status_code = post_response.status_code
        ret_err_text = post_response.text
    
    return isOk, ret_conversation_id, ret_content, ret_status_code, ret_err_text
