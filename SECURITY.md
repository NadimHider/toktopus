# Security Policy

## Supported Versions

We provide security updates and patches for the current release of toktopus:

| Version | Supported |
| :--- | :--- |
| 1.1.x | Yes |
| < 1.1.0 | No |

---

## Security Model

toktopus is designed to operate locally on your machine with minimal permissions:

* **Read-Only Local Inspection**: toktopus only reads existing session log files and process telemetry on your local machine. It does not modify session files or execute code on behalf of the agent.
* **No Telemetry Transmission**: toktopus does not transmit your prompts, code, conversation history, or token statistics to external servers. All token calculations and cost estimates occur strictly on your machine.
* **Optional Benchmark Refresh**: When explicitly requested, toktopus may fetch read-only benchmark data from public GitHub repositories using standard HTTPS requests.

---

## Reporting a Vulnerability

If you discover a security vulnerability in toktopus, please report it privately rather than opening a public issue.

Send vulnerability reports to:
* Email: nadimhider@gmail.com

Please include:
* Description of the issue
* Steps to reproduce
* Potential impact

We will review reports within 48 hours and work with you to release a fix promptly.
