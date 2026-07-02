"""
Phase 2 - Step 3: Verify Graph token actually works.
Calls /me to confirm identity and permissions.
"""
import requests
from teams_agent import get_token

def test_me():
    token = get_token()
    if not token:
        print("No token - aborting")
        return

    resp = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    if resp.status_code == 200:
        data = resp.json()
        print("SUCCESS")
        print("Name:", data.get("displayName"))
        print("Email:", data.get("mail") or data.get("userPrincipalName"))
    else:
        print("FAILED -", resp.status_code)
        print(resp.text)

if __name__ == "__main__":
    test_me()
