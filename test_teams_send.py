"""
Phase 2 - Step 4: Send a test Teams message to yourself.
Confirms Chat.ReadWrite / ChatMessage.Send actually work.
"""
import requests
from teams_agent import get_token

GRAPH = "https://graph.microsoft.com/v1.0"


def get_my_id(token):
    resp = requests.get(f"{GRAPH}/me", headers={"Authorization": f"Bearer {token}"})
    resp.raise_for_status()
    return resp.json()["id"]


def create_self_chat(token, my_id):
    body = {
        "chatType": "oneOnOne",
        "members": [
            {
                "@odata.type": "#microsoft.graph.aadUserConversationMember",
                "roles": ["owner"],
                "user@odata.bind": f"{GRAPH}/users('{my_id}')"
            }
        ]
    }
    resp = requests.post(f"{GRAPH}/chats", headers={"Authorization": f"Bearer {token}"}, json=body)
    if resp.status_code not in (200, 201):
        print("FAILED to create chat -", resp.status_code)
        print(resp.text)
        return None
    return resp.json()["id"]


def send_message(token, chat_id, text):
    body = {"body": {"content": text}}
    resp = requests.post(f"{GRAPH}/chats/{chat_id}/messages", headers={"Authorization": f"Bearer {token}"}, json=body)
    if resp.status_code not in (200, 201):
        print("FAILED to send message -", resp.status_code)
        print(resp.text)
        return False
    print("SUCCESS - message sent")
    return True


if __name__ == "__main__":
    token = get_token()
    if not token:
        print("No token - aborting")
    else:
        my_id = get_my_id(token)
        chat_id = create_self_chat(token, my_id)
        if chat_id:
            send_message(token, chat_id, "Cutover Agent test message - Phase 2 Step 4")
