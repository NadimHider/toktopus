"""Local metadata history. Polling updates snapshots, never adds token counters."""
import hashlib
import json
import math
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from toktopus.core.config import CONFIG_DIR

HISTORY_FILE = CONFIG_DIR / "history.sqlite3"
MAX_SESSIONS = 2000
MAX_EVENTS = 50000


def clean_text(value, limit=160):
    """Discard terminal controls and bound metadata. Never retain tool arguments."""
    return ''.join(c for c in str(value or '') if c.isprintable())[:limit]


class HistoryStore:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else HISTORY_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            pass
        else:
            os.close(fd)
        with closing(self._connect()) as db, db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS sessions (
                    agent TEXT NOT NULL, session_id TEXT NOT NULL,
                    model TEXT, updated REAL, observed REAL, snapshot TEXT,
                    PRIMARY KEY(agent, session_id));
                CREATE TABLE IF NOT EXISTS events (
                    agent TEXT NOT NULL, session_id TEXT NOT NULL,
                    event_id TEXT NOT NULL, observed REAL, data TEXT,
                    PRIMARY KEY(agent, session_id, event_id));
                CREATE INDEX IF NOT EXISTS events_session ON events(agent, session_id, observed);
            ''')

    def _connect(self):
        return sqlite3.connect(str(self.path), timeout=1)

    def record(self, agent, telemetry):
        sid = clean_text(telemetry.get('session_id'), 200)
        if not sid or sid in {'no-session', 'no-active-session', 'default', 'pi-session'}:
            return
        fields = ('input_tokens', 'output_tokens', 'cache_read_tokens', 'cache_write_tokens', 'cache_creation_tokens',
                  'reasoning_tokens', 'total_tokens', 'current_context_tokens',
                  'max_context_tokens', 'session_elapsed_sec', 'session_cost',
                  'is_active', 'current_context_available', 'tokens_per_sec_available')
        snapshot = {k: telemetry[k] for k in fields if k in telemetry and (telemetry[k] is None or isinstance(telemetry[k], (int, float)) and math.isfinite(telemetry[k]))}
        snapshot['data_status'] = clean_text(telemetry.get('data_status', 'locally observed'))
        snapshot['diagnostic_error'] = clean_text(telemetry.get('diagnostic_error'))
        events = []
        for step in telemetry.get('recent_steps', [])[-10000:]:
            event = {k: step[k] for k in ('index', 'input_tokens', 'output_tokens', 'total_tokens') if k in step and isinstance(step[k], (int, float)) and math.isfinite(step[k])}
            for key in ('type', 'status'):
                event[key] = clean_text(step.get(key), 60)
            if 'parent_id' in step:
                event['parent_id'] = clean_text(step['parent_id'], 100)
            if isinstance(step.get('duration_sec'), (int, float)) and math.isfinite(step['duration_sec']):
                event['duration_sec'] = step['duration_sec']
            if isinstance(step.get('timestamp'), (int, float)) and math.isfinite(step['timestamp']):
                event['timestamp'] = step['timestamp']
            tools = step.get('tools', [])
            if not isinstance(tools, list):
                tools = []
            event['tools'] = [clean_text(tool if isinstance(tool, str) else tool['name'], 80) for tool in tools[:20] if isinstance(tool, str) or isinstance(tool, dict) and isinstance(tool.get('name'), str)]
            # Token counts/status can be corrected later: identity uses source index.
            identity = clean_text(step['event_id'], 200) if step.get('event_id') else (str(step['index']) if 'index' in step else hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest())
            event['event_id'] = identity
            events.append((identity, event))
        now = time.time()
        with closing(self._connect()) as db, db:
            db.execute('INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?, ?)',
                       (agent, sid, clean_text(telemetry.get('model_name')), telemetry.get('last_modified', 0), now, json.dumps(snapshot)))
            for identity, event in events:
                db.execute('INSERT INTO events VALUES (?, ?, ?, ?, ?) ON CONFLICT(agent, session_id, event_id) DO UPDATE SET data=excluded.data',
                           (agent, sid, identity, now, json.dumps(event)))
            db.execute('DELETE FROM sessions WHERE rowid IN (SELECT rowid FROM sessions ORDER BY observed DESC LIMIT -1 OFFSET ?)', (MAX_SESSIONS,))
            db.execute('DELETE FROM events WHERE NOT EXISTS (SELECT 1 FROM sessions s WHERE s.agent=events.agent AND s.session_id=events.session_id)')
            db.execute('DELETE FROM events WHERE rowid IN (SELECT rowid FROM events ORDER BY observed DESC LIMIT -1 OFFSET ?)', (MAX_EVENTS,))

    def sessions(self, search='', limit=100, offset=0):
        # instr treats wildcard characters literally and parameters prevent SQL injection.
        with closing(self._connect()) as db:
            rows = db.execute('SELECT agent, session_id, model, updated, observed, snapshot FROM sessions WHERE instr(lower(agent || session_id || model), lower(?)) > 0 ORDER BY CASE WHEN updated > 0 THEN updated ELSE observed END DESC, agent, session_id LIMIT ? OFFSET ?', (search, min(max(limit, 1), MAX_SESSIONS), max(0, offset))).fetchall()
        return [dict(agent=r[0], session_id=r[1], model=r[2], updated=r[3], observed=r[4], snapshot=json.loads(r[5])) for r in rows]

    def timeline(self, agent, session_id):
        with closing(self._connect()) as db:
            rows = db.execute('SELECT data FROM events WHERE agent=? AND session_id=? ORDER BY observed, rowid', (agent, session_id)).fetchall()
        events = [json.loads(row[0]) for row in rows]
        # Imported/native timestamps establish chronology when every event has one.
        if events and all('timestamp' in event for event in events):
            events.sort(key=lambda event: (event['timestamp'], event.get('index', 0)))
        return events


def findings(events):
    """Deterministic evidence only; no LLM judgments or claims of task success."""
    failures = {}
    repeated = []
    last_tools, streak = None, 0
    for event in events:
        tools = tuple(event.get('tools', []))
        status = event.get('status', '').upper()
        if status in {'ERROR', 'FAILED', 'FAILURE'}:
            label = ', '.join(tools) or event.get('type') or 'Unknown operation'
            failures[label] = failures.get(label, 0) + 1
        streak = streak + 1 if tools and tools == last_tools else (1 if tools else 0)
        last_tools = tools
        if streak == 3:
            repeated.append(', '.join(tools))
    return failures, repeated
