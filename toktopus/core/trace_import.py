"""Read bounded OTLP/JSON exports without an SDK, collector or network service."""
import json
import math
from pathlib import Path

MAX_IMPORT_BYTES = 8_000_000
MAX_SPANS = 10000


def _number(value):
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError('Trace counters and timestamps must be finite and non-negative')
    return result


def _attributes(items):
    if not isinstance(items, list):
        raise ValueError('Attributes must be a list')
    result = {}
    for item in items:
        if not isinstance(item, dict) or not isinstance(item.get('value', {}), dict):
            raise ValueError('Malformed trace attribute')
        value = item.get('value', {})
        for kind in ('stringValue', 'intValue', 'doubleValue', 'boolValue'):
            if kind in value:
                result[item.get('key')] = value[kind]
                break
    return result


def import_otlp(path, store):
    """Import standard OTLP JSON span metadata. Prompts and arbitrary attrs omitted."""
    with Path(path).open('rb') as source:
        raw = source.read(MAX_IMPORT_BYTES + 1)
    if len(raw) > MAX_IMPORT_BYTES:
        raise ValueError('Trace import exceeds 8 MB')
    document = json.loads(raw)
    if not isinstance(document, dict) or not isinstance(document.get('resourceSpans'), list):
        raise ValueError('Expected an OTLP JSON resourceSpans document')
    sessions = {}
    count = 0
    for resource in document['resourceSpans']:
        if not isinstance(resource, dict) or not isinstance(resource.get('resource', {}), dict) or not isinstance(resource.get('scopeSpans', []), list):
            raise ValueError('Malformed resource spans')
        service = _attributes(resource.get('resource', {}).get('attributes', [])).get('service.name', 'otel')
        for scope in resource.get('scopeSpans', []):
            if not isinstance(scope, dict) or not isinstance(scope.get('spans', []), list):
                raise ValueError('Malformed scope spans')
            for span in scope.get('spans', []):
                if not isinstance(span, dict) or not isinstance(span.get('status', {}), dict):
                    raise ValueError('Malformed span')
                count += 1
                if count > MAX_SPANS:
                    raise ValueError('Trace import exceeds 10000 spans')
                trace_id, span_id = span.get('traceId'), span.get('spanId')
                if not trace_id or not span_id:
                    raise ValueError('Every span requires traceId and spanId')
                attrs = _attributes(span.get('attributes', []))
                start = _number(span.get('startTimeUnixNano', 0))
                end = _number(span.get('endTimeUnixNano', start))
                if end < start:
                    raise ValueError('Span ends before it starts')
                model = attrs.get('gen_ai.response.model') or attrs.get('gen_ai.request.model') or 'Unknown'
                key = (str(service), str(trace_id))
                telemetry = sessions.setdefault(key, {'session_id': str(trace_id), 'model_name': model, 'recent_steps': [], 'total_tokens': 0, 'data_status': 'imported OTLP metadata', 'current_context_available': False})
                input_tokens = int(_number(attrs.get('gen_ai.usage.input_tokens', 0)))
                output_tokens = int(_number(attrs.get('gen_ai.usage.output_tokens', 0)))
                # A trace can contain aggregate parents: never sum span counters into a session total.
                telemetry['total_tokens'] = None
                telemetry['recent_steps'].append({
                    'event_id': str(span_id), 'type': str(attrs.get('gen_ai.operation.name', 'span')),
                    'status': 'ERROR' if span.get('status', {}).get('code') in (2, 'STATUS_CODE_ERROR') else 'OBSERVED',
                    'tools': [str(attrs['gen_ai.tool.name'])] if attrs.get('gen_ai.tool.name') else [],
                    'input_tokens': input_tokens, 'output_tokens': output_tokens,
                    'total_tokens': input_tokens + output_tokens,
                    'parent_id': str(span.get('parentSpanId', '')), 'duration_sec': (end - start) / 1e9,
                })
    # Validate the whole file before persisting any trace.
    for (service, _), telemetry in sessions.items():
        store.record('otel:' + service, telemetry)
    return count
