# finget

[![PyPI](https://img.shields.io/pypi/v/finget.svg)](https://pypi.org/project/finget/)
[![Python](https://img.shields.io/pypi/pyversions/finget.svg)](https://pypi.org/project/finget/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Official **Python** SDK for the [Finget](https://finget.ir) public API (`/api/v1`).

Use it on your server to:

- Start **passwordless login** (“Sign in with Finget”)
- Exchange the one-time callback `code` for a Finget user
- Send **push notifications** to linked users
- Inspect site and notification delivery status

Zero third-party dependencies (stdlib `urllib` only).

> Keep your API key on the server only. Never expose `FINGET_API_KEY` in browsers or mobile apps.

## Links

| | |
|---|---|
| Website | [finget.ir](https://finget.ir) |
| Plugins & SDKs | [finget.ir/plugins](https://finget.ir/plugins) |
| API docs | [Provider panel docs](https://finget.ir/provider/panel/docs) |
| PyPI | [pypi.org/project/finget](https://pypi.org/project/finget/) |
| Repository | [amirsafaridevs/finget-python](https://github.com/amirsafaridevs/finget-python) |

## Requirements

- Python **3.10+**

## Installation

```bash
pip install finget
```

```bash
uv add finget
poetry add finget
```

## Quick start

```bash
export FINGET_API_KEY=fg_live_...
```

```python
from finget import Client

finget = Client.from_env()
# or: Client(api_key=os.environ["FINGET_API_KEY"])

site = finget.get_site()
# site["site"] → domain, displayDomain, name, verifiedAt
```

## Authentication (Sign in with Finget)

1. In the Finget provider panel, copy your **site client ID** and register the callback URL.
2. Redirect the user to Finget with a CSRF `state` stored in the session.
3. On callback, verify `state`, then exchange `code`.

Example with a Flask-style flow:

```python
from flask import Flask, redirect, request, session
from finget import Client, ApiError

app = Flask(__name__)
finget = Client.from_env()
CLIENT_ID = os.environ["FINGET_CLIENT_ID"]

@app.get("/login/finget")
def login_start():
    login = finget.login_url(CLIENT_ID)
    session["finget_state"] = login["state"]
    return redirect(login["url"])

@app.get("/auth/finget/callback")
def login_callback():
    expected = session.pop("finget_state", "")
    code = request.args.get("code", "")
    state = request.args.get("state", "")

    if not code or not expected or state != expected:
        return redirect("/login")

    try:
        result = finget.exchange_code(code)
    except ApiError:
        return redirect("/login")

    user = result["user"]  # id, name, phone
    is_new = result["isNew"]
    # Find or create your local account by user["id"], then establish a session.
    return redirect("/")
```

### `login_url()`

```python
login = finget.login_url(client_id)              # generates state
login = finget.login_url(client_id, state=state) # reuse your own state
# {"url": "https://finget.ir/auth?...", "state": "..."}
```

## Notifications

```python
result = finget.send_notification({
    "id": f"order-{order_id}-shipped",  # optional idempotency key
    "kind": "notice",  # notice | reminder | security | promo
    "title": "Your order shipped",
    "body": f"Order {order_id} is on the way.",
    "link": {
        "url": f"https://shop.example/orders/{order_id}",
        "label": "Track order",
    },
    "users": [user["id"]],
    # or: "audience": "all",
})
```

Optional coupon:

```python
"coupon": {
    "code": "SAVE10",
    "note": "Valid this week",
    "expiresAt": "2026-12-31T23:59:59+03:30",
}
```

Check status later:

```python
status = finget.get_notification("order-1234-shipped")
```

## API reference

| Method | Description |
|--------|-------------|
| `Client.from_env(api_key_env="FINGET_API_KEY")` | Build from environment variables |
| `get_site()` | Validate the API key; return site info |
| `login_url(client_id, state=None)` | Auth redirect URL + state |
| `create_state(nbytes=16)` | Cryptographically secure hex state |
| `exchange_code(code)` | Exchange callback code → `{user, isNew}` |
| `get_user(user_id)` | Refresh a linked user’s profile |
| `send_notification(payload)` | Create a notification (HTTP 201) |
| `get_notification(notification_id)` | Notification status / recipients |

### Constructor

```python
Client(
    api_key,
    base_url="https://finget.ir/api/v1",
    auth_url="https://finget.ir/auth",
    timeout=20.0,  # seconds
)
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FINGET_API_KEY` | yes (for `from_env`) | Site API key (`fg_live_…`) |
| `FINGET_BASE_URL` | no | Override API base URL |
| `FINGET_AUTH_URL` | no | Override login page URL |

## Error handling

```python
from finget import Client, ApiError, FingetError

try:
    Client.from_env().get_site()
except ApiError as e:
    e.args[0]      # message
    e.status       # 0 if transport failed
    e.error_code   # e.g. invalid_api_key when present
    e.body         # decoded JSON body
except FingetError:
    # Client-side validation (empty key, empty code, …)
    ...
```

## Local development

```python
finget = Client(
    api_key=os.environ["FINGET_API_KEY"],
    base_url="http://localhost:3001/api/v1",
    auth_url="http://localhost:5173/auth",
)
```

Or set `FINGET_BASE_URL` / `FINGET_AUTH_URL` before `Client.from_env()`.

## License

[MIT](LICENSE)
