"""Deterministic impact engine for normalized API contracts (not OpenAPI)."""
from collections import deque


def validate(payload):
    if not isinstance(payload, dict):
        raise ValueError('Request must be an object')
    if not isinstance(payload.get('service'), str) or not payload['service'].strip():
        raise ValueError('service must be a nonempty string')
    for version in ('before', 'after'):
        contract = payload.get(version)
        if not isinstance(contract, dict):
            raise ValueError(version + ' must be an endpoint map')
        for endpoint, fields in contract.items():
            if not isinstance(endpoint, str) or not endpoint.strip() or not isinstance(fields, dict):
                raise ValueError('Endpoints must map names to response field maps')
            if any(not isinstance(k, str) or not k or v not in ('string', 'integer', 'number', 'boolean', 'object', 'array') for k, v in fields.items()):
                raise ValueError('Fields must use supported JSON type names')
    graph = payload.get('dependencies', {})
    if not isinstance(graph, dict) or any(not isinstance(k, str) or not k or not isinstance(v, list) or any(not isinstance(s, str) or not s for s in v) for k, v in graph.items()):
        raise ValueError('dependencies must map consumer services to provider name lists')


def analyze(payload):
    validate(payload)
    before, after = payload['before'], payload['after']
    findings = []
    def add(code, endpoint, field=None):
        findings.append(dict(code=code, endpoint=endpoint, field=field, severity='HIGH'))
    for endpoint, fields in sorted(before.items()):
        if endpoint not in after:
            add('ENDPOINT_REMOVED', endpoint)
            continue
        for field, old_type in sorted(fields.items()):
            if field not in after[endpoint]:
                add('RESPONSE_FIELD_REMOVED', endpoint, field)
            elif after[endpoint][field] != old_type:
                add('RESPONSE_TYPE_CHANGED', endpoint, field)
    reverse = {}
    for consumer, providers in payload.get('dependencies', {}).items():
        for provider in providers:
            reverse.setdefault(provider, set()).add(consumer)
    origin = payload['service']
    seen, queue, affected = {origin}, deque([(origin, [origin])]), []
    while queue:
        provider, path = queue.popleft()
        for consumer in sorted(reverse.get(provider, ())):
            if consumer not in seen:
                seen.add(consumer)
                trail = path + [consumer]
                affected.append(dict(service=consumer, distance=len(trail)-1, path=trail))
                queue.append((consumer, trail))
    changed = before != after
    risk = 'HIGH' if findings else ('LOW' if changed else 'NONE')
    return dict(service=origin, risk=risk, breakingChanges=findings,
                potentialConsumers=affected if changed else [],
                recommendedTests=[f'Run consumer contract tests: {item["service"]} -> {origin}' for item in affected if item['distance'] == 1 and changed],
                requiresReview=bool(findings),
                limitations=['Normalized response contracts only; no request, enum, nullable, nested schema or OpenAPI analysis.',
                             'Service dependencies indicate potential impact, not proven endpoint usage.',
                             'Additive fields are treated as low risk; strict clients may reject them.'])
