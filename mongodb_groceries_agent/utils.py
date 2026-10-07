import os

import requests

KEY_ENDPOINT = "https://adk-workshop-480093582215.europe-west1.run.app/"


def set_env(passkey: str) -> None:
    """Exchange the workshop passkey for credentials and put them in os.environ.

    Args:
        passkey: The passkey your instructor gives you.
    """
    response = requests.post(url=KEY_ENDPOINT, json={"passkey": passkey}, timeout=30)

    if response.status_code == 200:
        for key, value in response.json().items():
            os.environ[key] = value
        return

    # The endpoint is not consistent about which key carries the reason, and on
    # some failures the body is not JSON at all. Fall back rather than raising a
    # KeyError that tells the reader nothing about what actually went wrong.
    try:
        body = response.json()
        detail = body.get("error") or body.get("message") or response.text
    except ValueError:
        detail = response.text

    if response.status_code == 401:
        raise RuntimeError(
            f"The passkey was not accepted ({detail}). Ask your instructor for the passkey."
        )

    raise RuntimeError(
        f"Could not reach the workshop key service (HTTP {response.status_code}): {detail}"
    )
