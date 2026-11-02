# Local observability design and reference review

Reviewed 2026-11-02. This compares public READMEs for all 15 requested projects,
with additional source inspection of AgentOps exporters, agentplay's native
parsers/store/span model, claude-tap's trace store, and AgentSight's event/export
schemas. It is an architecture review, not a security audit or a claim that every
feature has been exercised. No reference project is installed as a runtime dependency.

## Product contract

Toktopus runs in the terminal, requires no monitoring-service account, and issues
no model requests. Monitoring has zero additional inference/API charges. Existing
coding-agent subscriptions/API charges, hardware, storage and electricity remain
the user's responsibility. Offline operation is the default. The only new outbound
request is an explicit public LiveNerf refresh.

Automatic visibility is limited to what supported local transcripts, databases,
and processes expose. Authentication cannot solve missing telemetry. Remote work
without local records, provider billing, hidden thoughts, and definitive task
success are unavailable unless a supported evidence source supplies them.

## Reference matrix

| Reference | Mechanism / useful lesson | Toktopus application | Constraint |
|---|---|---|---|
| [AgentOps](https://github.com/AgentOps-AI/agentops) | Provider/framework instrumentation, nested spans, session analytics; SDK exporter subclasses OTLP HTTP exporter and adds JWT handling | Preserve session/event identities and parent relationships; accept local OTLP JSON | Default onboarding uses an AgentOps API key; importing SDK does not automatically instrument unrelated processes |
| [Latitude](https://github.com/latitude-dev/latitude-llm) | Issue-centric grouping, agent traces, aligned evaluations, semantic search | Group observed tool failures and distinguish deterministic checks from semantic judgment | Semantic evaluations/search may need inference; LGPL code is not copied |
| [Logfire](https://github.com/pydantic/logfire) | OpenTelemetry traces/metrics/logs, SQL exploration, Python instrumentation | Open format import and local SQLite queries | Open SDK, closed-source UI/server; enterprise self-host is not a free embedded backend |
| [Laminar](https://github.com/lmnr-ai/lmnr) | OTel-native traces, SQL dashboards, datasets, evals, signals | Queryable local history, optional later dataset export | Its Compose backend is a separate stack; AI workers need an LLM provider; self-host telemetry needs explicit opt-out |
| [Agenta](https://github.com/Agenta-AI/agenta) | Agent workspace, traceability, evaluation/model configuration, self-hosting | Compare model/session measurements with explicit configuration provenance | Building/running agents is different from passive observation; no automatic orchestration in Toktopus |
| [LangWatch](https://github.com/langwatch/langwatch) | Coding-agent ingestion, traces, evaluation, gateway, governance | Agent source coverage and cost attribution as explicit capabilities | Gateway routing/virtual budgets require controlling traffic; enterprise modules are separately licensed |
| [claude-tap](https://github.com/liaohch3/claude-tap) | Reverse/forward proxy capture plus native transcripts; bounded SQLite trace queries | Prefer native transcript evidence; local storage, failure isolation and explicit imports | Proxy capture changes agent launch/traffic; TLS capture can require trusting a local CA; not automatic/default here |
| [TraceRoot](https://github.com/traceroot-ai/traceroot) | Detectors -> improvement signals -> investigation -> offline verification | Deterministic findings tied to trace evidence | Automatic fixing/evaluating invokes agents/models; excluded from the zero-inference path |
| [AgentSight](https://github.com/eunomia-bpf/agentsight) | Native sources plus kernel/process/TLS correlation, versioned nullable export schema | Separate process evidence from model events; preserve missing values | eBPF capture needs Linux and privileges; native fallback is cross-platform; not universal TLS visibility on Windows |
| [PandaProbe](https://github.com/chirpz-ai/pandaprobe) | Trace/session/span APIs; queued ingestion; eval workers | Separate ingestion, persistence and terminal presentation | Its full stack includes auth, Postgres, Redis, Celery and LLM judges; not embedded |
| [Agenttrail](https://github.com/sodiumsun/agenttrail) | Local session discovery, project map, native task state, optional hooks | Evidence-first progress and activity; no inferred completion from a turn ending | Cross-session handoffs need metadata; 3D browser rendering is not terminal functionality |
| [AgentRails](https://github.com/rforgeon/AgentRails) | n8n execution history/dashboard | Execution-status distinctions and filters | n8n/API credentials and Anthropic key are required for its advertised setup; not a generic passive agent collector |
| [Agent Monitor](https://github.com/cogniolab/agent-monitor) | SDK agent/task tracing, token/cost metrics and dashboard | Session/operation views and per-source metrics | SDK instrumentation and API-key examples do not imply automatic whole-machine visibility |
| [agentplay](https://github.com/Entelligence-AI/agentplay) | Native transcript discovery -> universal spans -> incremental local maps/index; replay and failure analysis | Stable tool identities, tool/result pairing, metadata-only timelines | Source fidelity differs by agent; full maps/task/file attribution require richer parsers than current Toktopus |
| [agent-observability](https://github.com/fmelihh/agent-observability) | Instrumented LangGraph example, OTel, Prometheus counters/histograms, Grafana | Keep cumulative counters distinct from observations and rate windows | Example agent requires OpenAI; Docker/Grafana stack is unnecessary for a terminal viewer |

## Implemented in this change

- Account limits now return unavailable values rather than converting session
  volume into fictional minute quotas. Configured plan tables remain legacy
  estimates, never verified account data.
- Codex and Copilot identities are separated. Codex inclusive input/cache and
  output/reasoning semantics avoid double-counting totals and cost components.
- Fabricated speeds and Pi demo token/tool activity are removed.
- Local diagnostics, persistent session snapshots, metadata search and observed
  tool timelines. Re-polling replaces totals and updates events; it never adds
  cumulative totals again. History defaults to at most 2,000 sessions/50,000 events.
- Detected agents are polled for history every five seconds; selected agent
  readings are cached for two seconds. One failing reader cannot stop the others.
- Claude/Codex native tool/result pairing, including custom Codex tools. Only
  explicit error flags/exit-code evidence mark a tool as failed.
- OpenCode session/message/part schema reader, with read-only database access,
  per-message usage and tool-state extraction; legacy session_v2 fallback retained.
- Failure counts and three-consecutive-tool-activity hints. A hint is not a
  semantic failure verdict. Polling may omit events; this is not a full replay.
- Bounded OTLP JSON file import: trace/span/parent identity, duration, tool names,
  token attributes and explicit error status. This is not an OTLP network receiver,
  not a protobuf importer, and not automatic SDK instrumentation. Nested span
  counters are not summed into invented trace totals.
- Public LiveNerf reader with validation, content digest, retrieval timestamp,
  offline cache and explicit refresh. Aggregate/family rows are not summed.

## Remaining work, in dependency order

1. Broader native parser coverage: real Pi coding-agent JSONL, Gemini CLI and
   separate Copilot; fixtures pinned to real versions and native-install validation
   of the OpenCode session/message/part reader.
   Current unsupported schemas show diagnostics, not fabricated support.
2. Incremental native ingestion with persisted file cursors, truncation/rotation
   recovery, duplicate streamed-message reconciliation, archived sessions and
   subagents. Current readers retain bounded recent observations only.
3. Project/file/task relationships, repo filtering, tool categories, actual tool
   latencies, percentile panels and deterministic annotations. Attribute file
   edits/tasks only from explicit tool evidence; never invent authorship or success.
4. Local loopback OTLP receiver and opt-in SDK/hook bridges with exporter recipes.
   A running app must emit/export spans before Toktopus can see them.
5. Read-only import adapters for external replay exports. Validate version/license
   and privacy fields before using an upstream format. No silent installation.
6. Local dataset export, deterministic evaluators, saved comparisons, annotations
   and local-model integration only if explicitly enabled. No automatic paid judge,
   benchmark run, agent dispatch or prompt execution.
7. Optional Linux eBPF/export integration, optional proxy-launch mode, Prometheus
   export and deeper OS activity. Neither certificate installation nor privileged
   tracing belongs in default startup.

This coverage intentionally does not claim feature parity with fifteen platforms.
The architecture supports expansion while preserving a no-login, zero-inference
default. Reuse concepts and open formats; review actual licenses before copying
any upstream implementation.

## Privacy and limitations

History stores session/model identifiers, counters, event status, tool names,
parent IDs and durations. It omits prompts, tool arguments, tool outputs,
arbitrary imported span attributes and environment variables. Metadata can still
be sensitive. Existing native adapters may read transcripts locally and legacy
snapshot exports may contain session details; review before sharing.

Use `--no-history` to disable recording and automatic discovery. No cloud upload,
telemetry service, credential-store access or inference is added. Retention bounds
row counts, not physical SQLite file bytes. Delete the app-owned history database
manually when the app is stopped if you want to remove recorded metadata.
