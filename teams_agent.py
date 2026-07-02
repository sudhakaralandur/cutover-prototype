"""
Phase 2 - Step 2: MSAL device code flow.
Logs in as the actual user (sudhakar.alandur@outlook.com) via browser code.
Caches token so repeat runs don't require re-login until it expires.
"""
import os
import json
import msal
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("MSAL_CLIENT_ID")
TENANT_ID = os.getenv("MSAL_TENANT_ID")
SCOPE = os.getenv("MSAL_SCOPE", "Chat.ReadWrite,ChatMessage.Send,User.Read").split(",")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
CACHE_FILE = "token_cache.bin"


def load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        cache.deserialize(open(CACHE_FILE, "r").read())
    return cache


def save_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def get_token():
    cache = load_cache()
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )

    accounts = app.get_accounts()
    result = None
    if accounts:
        result = app.acquire_token_silent(SCOPE, account=accounts[0])

    if not result:
        flow = app.initiate_device_flow(scopes=SCOPE)
        if "user_code" not in flow:
            print("FAILED to create device flow")
            print(flow)
            return None
        print(flow["message"])
        result = app.acquire_token_by_device_flow(flow)

    save_cache(cache)

    if result and "access_token" in result:
        print("SUCCESS - got access token")
        print("Token starts with:", result["access_token"][:20], "...")
        return result["access_token"]
    else:
        print("FAILED to get token")
        print("Error:", result.get("error") if result else "no result")
        print("Description:", result.get("error_description") if result else "")
        return None


if __name__ == "__main__":
    get_token()
