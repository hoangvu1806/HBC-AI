
def chat_with_leave_request_agent(user_name, user_email, refresh_token,message: str):
    url = "http://localhost:5680/chat"
    return request.post(url, json={
        "user_email": user_email,
        "prompt": message,
        "user_name": user_name,
        "refresh_token": refresh_token
    })
