"""Terminal session history and observed event timelines."""
from datetime import datetime, timezone

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from toktopus.core.history import findings


def render_history(store, search='', limit=100, selected=None, offset=0):
    table = Table(title='Local session history', expand=True)
    for label in ('Agent', 'Session', 'Model', 'Tokens', 'State'):
        table.add_column(label)
    rows = store.sessions(search, limit=limit, offset=offset)
    for index, row in enumerate(rows):
        snap = row['snapshot']
        tokens = snap.get('total_tokens')
        table.add_row(Text(row['agent']), Text(row['session_id']), Text(row['model']), str(tokens) if tokens is not None else 'Unavailable', Text(snap.get('data_status', 'observed')), style='bold cyan' if index == selected else None)
    note = f'Sessions {offset + 1} to {offset + len(rows)}. ' if rows else 'No recorded sessions on this page. Run the dashboard to collect available local activity. '
    note += 'Latest snapshots, not sums of refreshes. Metadata only; prompts and tool arguments are not stored.'
    return Panel(Group(Text(note), table), subtitle='[ ] Select | Enter Timeline | N/P Pages | J Overview | Q Quit')


def render_timeline(store, agent, session_id, limit=200, offset=0, compact=False):
    events = store.timeline(agent, session_id)
    table = Table(title=Text(f'{agent}: {session_id[:32]} (observed events)'), expand=True)
    columns = ('Time (UTC)', 'Status', 'Tools', 'Tokens') if compact else ('Time (UTC)', 'Step / span', 'Type', 'Status', 'Tools', 'Tokens', 'Duration', 'Parent')
    for label in columns:
        table.add_column(label)
    end = max(0, len(events) - max(0, offset))
    visible = events[max(0, end - limit):end]
    for event in visible:
        try:
            timestamp = datetime.fromtimestamp(event['timestamp'], tz=timezone.utc).strftime('%H:%M:%S' if compact else '%Y-%m-%d %H:%M:%S')
        except (KeyError, ValueError, OSError, OverflowError):
            timestamp = 'Unavailable'
        cells = [timestamp, Text(event.get('status', '')), Text(', '.join(event.get('tools', []))), str(event.get('total_tokens', 'Unavailable'))]
        if not compact:
            cells = [timestamp, Text(str(event.get('index', event.get('event_id', '?')))), Text(event.get('type', '')), *cells[1:], str(event.get('duration_sec', 'Unavailable')), Text(event.get('parent_id', ''))]
        table.add_row(*cells)
    failures, repeated = findings(events)
    note = Text(f'Showing {len(visible)} of {len(events)} observed events, skipping {offset} newest events. Failed operations: {sum(failures.values())}.\n')
    for name, count in failures.items():
        note.append(f'{name}: {count} failures\n')
    for tools in repeated:
        note.append(f'Repeated activity: {tools} (3 consecutive events; inspect for a possible loop)\n')
    note.append('Polling may miss events between observations. This is recorded evidence, not re-execution or proof of task completion.')
    return Panel(Group(table, note), subtitle='N Older | P Newer | J History | Q Quit')
