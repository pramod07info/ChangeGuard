# ChangeGuard AI — first implementation

A runnable, dependency-free impact-analysis backend. Python 3.10+ required.
The first slice uses deterministic rules; an LLM has not been integrated.

## Run

```sh
cd ChangeGuard
python3 -m unittest discover -s tests -v
python3 server.py
```

Windows: use `python` instead of `python3`.
From another terminal in the same directory:

```sh
curl -H "Content-Type: application/json" --data-binary @examples/change.json http://127.0.0.1:8080/api/v1/impact
```

GET `/health` returns service status. POST `/api/v1/impact` accepts before/after
normalized response contracts and a dependency graph. Graph edges mean
consumer -> providers. Returns removed endpoints, removed fields, changed
types, reachable consumers, one shortest impact path, risk and test suggestions.
The sample removes payment amount and flags orders, checkout and notifications.

## Scope and next steps

This is a local development MVP, not enterprise-ready deployment.
It does not parse OpenAPI, inspect Git diffs or execute tests. No authentication,
database, UI, integrations, deployment approval or LLM inference is included.
Review flags are advisory. Service-level reachability does not prove a consumer
uses a changed endpoint. Nested schemas, request compatibility and strict
client behavior require subsequent analysis.

Next bounded step: import OpenAPI contracts with directional request/response
compatibility checks, then add repository adapters. A Spring Boot API can host
the same analysis model when the Java build environment is available.
