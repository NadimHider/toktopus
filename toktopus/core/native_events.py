"""Bounded local transcript metadata reader for replay without prompt retention."""
import json
import re
from pathlib import Path

MAX_BYTES = 16_000_000
EXIT_CODE = re.compile(r'^Process exited with code (\d+)\s*$', re.MULTILINE)


def read_native_events(path, agent):
    """Return tool-call evidence; never execute or persist arguments or outputs."""
    events, calls = [], {}
    skipped = 0
    with Path(path).open('rb') as source:
        data = source.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Transcript exceeds 16 MB; use a smaller export')
    for index, line in enumerate(data.splitlines(), 1):
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError('Record must be an object')
            if agent == 'codex':
                payload = record.get('payload') or {}
                kind = payload.get('type')
                if record.get('type') != 'response_item':
                    continue
                if kind in ('function_call', 'custom_tool_call'):
                    event = {'index': index, 'event_id': 'native:' + str(index), 'type': 'TOOL_CALL', 'status': 'OBSERVED', 'tools': [payload.get('name', 'tool')]}
                    calls[payload.get('call_id', str(index))] = event
                    events.append(event)
                elif kind in ('function_call_output', 'custom_tool_call_output'):
                    event = calls.get(payload.get('call_id'))
                    if event is not None:
                        output = payload.get('output', '')
                        if isinstance(output, str):
                            match = EXIT_CODE.search(output)
                            if match:
                                event['status'] = 'ERROR' if int(match[1]) else 'DONE'
            elif agent == 'claude':
                for block in (record.get('message') or {}).get('content', []):
                    if not isinstance(block, dict):
                        continue
                    if block.get('type') == 'tool_use':
                        event = {'index': index, 'event_id': 'native:' + str(block.get('id', index)), 'type': 'TOOL_CALL', 'status': 'OBSERVED', 'tools': [block.get('name', 'tool')]}
                        calls[block.get('id', str(index))] = event
                        events.append(event)
                    elif block.get('type') == 'tool_result':
                        event = calls.get(block.get('tool_use_id'))
                        if event is not None:
                            event['status'] = 'ERROR' if block.get('is_error') else 'DONE'
        except (ValueError, TypeError, AttributeError):
            skipped += 1
    return events, skipped
