import requests
import os

KEY_ENDPOINT = "https://adk-workshop-480093582215.europe-west1.run.app/"

def set_env(passkey: str) -> None:
    """
    Set environment variables in sandbox

    Args:
        passkey (str): Passkey to get token
    """
    payload = {"passkey": passkey}
    response = requests.post(url=KEY_ENDPOINT, json=payload)
    status_code = response.status_code
    if status_code == 200:
        result = response.json()
        for key in result:
            os.environ[key] = result[key]
    elif status_code == 401:
        raise Exception(f"{response.json()['error']} Ask your instructor for the passkey.")
    else:
        raise Exception(f"{response.json()['error']}")
