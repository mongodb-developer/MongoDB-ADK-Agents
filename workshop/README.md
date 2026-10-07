# Workshop files

The lab ships a stripped-down version of the agent that attendees fill in. Those
files live here, so the VM image never hand-edits anything and the exercise is
version-controlled alongside the finished code.

## Layout

| Path | What it is |
|---|---|
| `starter/` | What attendees start from. Copied over `mongodb_groceries_agent/` at image build time. |
| `solutions/` | The cumulative state of `agent.py` after each challenge. For instructors, and for the track's check scripts. |
| `generate_solutions.py` | Regenerates `solutions/` from `mongodb_groceries_agent/agent.py`. |

`mongodb_groceries_agent/` itself stays complete and runnable. It is the path
the published tutorial uses, and `git clone && adk web` has to keep working.

## Solutions are generated, not written

Each solution is the same file at a different stage, so maintaining four copies
by hand means applying every fix four times. They are derived from the finished
agent instead:

```bash
python3 workshop/generate_solutions.py
```

CI runs `--check`, which fails if a solution was edited directly or if
`agent.py` changed without regenerating. **Change `agent.py`, then regenerate.**

The stages map onto the track's challenges:

| Solution | Challenge |
|---|---|
| `01-bare-agent.py` | 02: an agent with no tools |
| `02-vector-search.py` | 03: `find_similar_products` |
| `03-filtered-search.py` | 04: category pre-filter |
| `04-cart-tools.py` | 05: `add_to_cart`, `calculate_cart_total` |

`04-cart-tools.py` is `mongodb_groceries_agent/agent.py` with the passkey
preamble swapped in; the agent code is identical.

## Placeholders

`starter/` files carry `<PLACEHOLDER>` markers that attendees replace. CI asserts
they are still present, because losing one means shipping an answer, and asserts
that `mongodb_groceries_agent/` has none, because the tutorial path must run
as-is.

## The passkey

`starter/agent.py` calls `set_env(PASSKEY)` from `mongodb_groceries_agent/utils.py`,
which exchanges the passkey for `GOOGLE_API_KEY` and `CONNECTION_STRING` against a
Cloud Run service. That service is deployed outside this repo. Confirm it is up
before a workshop:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -X POST \
  -H 'Content-Type: application/json' \
  -d '{"passkey":"invalid"}' \
  https://adk-workshop-480093582215.europe-west1.run.app/
# 401 means the service is up and rejecting bad passkeys, which is what you want.
```
