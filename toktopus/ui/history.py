"""Terminal session history and observed event timelines."""
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from toktopus.core.history import findings


def render_history(store, search='', limit=100, selected=None):
    table = Table(title='Local session history', expand=True)
    for label in ('Agent', 'Session', 'Model', 'Tokens', 'State'):
        table.add_column(label)
    for index, row in enumerate(store.sessions(search, limit=limit)):
        snap = row['snapshot']
        tokens = snap.get('total_tokens')
        table.add_row(Text(row['agent']), Text(row['session_id']), Text(row['model']), str(tokens) if tokens is not None else 'Unavailable', Text(snap.get('data_status', 'observed')), style='bold cyan' if index == selected else None)
    return Panel(Group(Text('Session totals are latest snapshots, not sums of refreshes. Metadata search only; prompts and tool arguments are not stored.'), table), subtitle='[ ] Select | Enter Timeline | J Overview | Q Quit')


def render_timeline(store, agent, session_id, limit=200):
    events = store.timeline(agent, session_id)
    table = Table(title='Observed timeline (available events only)', expand=True)
    for label in ('Step', 'Type', 'Status', 'Tools', 'Tokens', 'Duration', 'Parent'):
        table.add_column(label)
    for event in events[-limit:]:
        table.add_row(str(event.get('index', '?')), Text(event.get('type', '')), Text(event.get('status', '')), Text(', '.join(event.get('tools', []))), str(event.get('total_tokens', 'Unavailable')), str(event.get('duration_sec', 'Unavailable')), Text(event.get('parent_id', '')))
    failures, repeated = findings(events)
    note = Text(f'Showing the latest {min(limit, len(events))} of {len(events)} observed events. Failed operations: {sum(failures.values())}.\n')
    for name, count in failures.items():
        note.append(f'{name}: {count} failures\n')
    for tools in repeated:
        note.append(f'Repeated activity: {tools} (3 consecutive events; inspect for a possible loop)\n')
    note.append('Polling may miss events between observations. This is recorded evidence, not re-execution or proof of task completion.')
    return Panel(Group(table, note), subtitle='J History | D Diagnostics | H Model Health | Q Quit')
