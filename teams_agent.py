"""
Phase 2 - Step 1: MSAL auth test.
Confirms we can get an access token from MS Graph before adding Teams logic.
"""
import os
import msal
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("MSAL_CLIENT_ID")
TENANT_ID = os.getenv("MSAL_TENANT_ID")
CLIENT_SECRET = os.getenv("MSAL_CLIENT_SECRET")

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]

def get_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(scopes=SCOPE)

    if "access_token" in result:
        print("SUCCESS - got access token")
        print("Token starts with:", result["access_token"][:20], "...")
        return result["access_token"]
    else:
        print("FAILED to get token")
        print("Error:", result.get("error"))
        print("Description:", result.get("error_description"))
        return None

if __name__ == "__main__":
    get_token()
