"""Download public reference documentation for a local, read-only comparison."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

REPOS = ['AgentOps-AI/agentops', 'latitude-dev/latitude-llm', 'pydantic/logfire', 'lmnr-ai/lmnr', 'Agenta-AI/agenta', 'langwatch/langwatch', 'liaohch3/claude-tap', 'traceroot-ai/traceroot', 'eunomia-bpf/agentsight', 'chirpz-ai/pandaprobe', 'sodiumsun/agenttrail', 'rforgeon/AgentRails', 'cogniolab/agent-monitor', 'Entelligence-AI/agentplay', 'fmelihh/agent-observability']


def fetch(repo):
    for branch in ('main', 'master'):
        try:
            url = f'https://raw.githubusercontent.com/{repo}/{branch}/README.md'
            with urlopen(url, timeout=15) as response:
                content = response.read(200_000).decode('utf-8')
            path = Path('.research') / (repo.replace('/', '__') + '.md')
            path.parent.mkdir(exist_ok=True)
            path.write_text(content, encoding='utf-8')
            return f'{repo}: {len(content)} chars saved'
        except HTTPError as exc:
            if exc.code != 404:
                return f'{repo}: HTTP {exc.code}'
    return f'{repo}: README unavailable'


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=8) as pool:
        for result in pool.map(fetch, REPOS):
            print(result)
