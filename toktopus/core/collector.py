"""Rate-limited local polling, with independent agent failures."""
import sqlite3
import time

from toktopus.adapters import get_adapter

AGENTS = ('antigravity', 'claude', 'opencode', 'cursor', 'codex', 'pi')


class LocalCollector:
    def __init__(self):
        self.adapters = {}
        self.snapshots = {}
        self.checked = {}

    def poll(self, agent, force=False):
        now = time.monotonic()
        if not force and agent in self.snapshots and agent in self.checked and now - self.checked[agent] < 2:
            return self.snapshots[agent]
        try:
            if agent not in self.adapters:
                self.adapters[agent] = get_adapter(agent)
            adapter = self.adapters[agent]
            telemetry = adapter.get_session_telemetry()
            telemetry.setdefault('tokens_per_sec_available', False)
            if telemetry.get('session_id') in (None, 'no-session', 'no-active-session', 'pi-session'):
                telemetry.setdefault('data_status', 'no-session')
                telemetry.setdefault('current_context_available', False)
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError, RuntimeError) as exc:
            telemetry = {'agent_name': agent, 'session_id': 'no-session', 'data_status': 'error', 'diagnostic_error': f'Local reader failed ({type(exc).__name__})', 'is_active': False}
        self.snapshots[agent] = telemetry
        self.checked[agent] = now
        return telemetry

    def poll_detected(self):
        for agent in AGENTS:
            try:
                if agent not in self.adapters:
                    self.adapters[agent] = get_adapter(agent)
                if self.adapters[agent].is_detected():
                    self.poll(agent)
            except (OSError, ValueError, TypeError, RuntimeError):
                continue
        return dict(self.snapshots)
