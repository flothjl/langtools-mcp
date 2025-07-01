# langtools-mcp: Multi-Language Code Analysis Sidecar for Agents & Automation

## Overview

**langtools-mcp** is a modular, multi-language code analysis and static-check sidecar for agents, LLMs, CI/CD, and developer automation.  
It orchestrates best-in-class language tools (like [Ruff](https://github.com/astral-sh/ruff), gopls, rust-analyzer, and more) using a robust daemon architecture.

**Key Features:**
- 🔗 **Unified API:** One protocol/entrypoint for diverse language toolchains and linters
- 🔄 **Automatic Sidecar Management:** Daemon is launched and cleaned up for you
- ⛓️ **Designed for scale:** Supports multi-lang codebases and batch processing
- 🔜 **Future-Ready:** Easily extend with new language tools

---

## Architecture

```text
+-------------------------------+               HTTP (localhost)               +-------------------------------+
|     langtools-mcp (MCP)       | <-----------------------------------------> |   langtools_daemon sidecar     |
+-------------------------------+                                               +-------------------------------+
                                                                                          |
                                                                                     (runs linters)
                                                                                          v
                                                                            ruff, gopls, rust-analyzer, etc.
```

When you launch the main server or CLI, `langtools_daemon` is started automatically and managed as a subprocess.  
All analysis requests—regardless of the underlying language—are routed to this sidecar, which coordinates the appropriate language tools.

---

## Features

- **Multi-language support:** Python (Ruff) ready now; Go, Rust, and others coming soon
- **Decoupled code analysis:** No need for IDEs, editors, or direct dependency on any single tool
- **Headless & batch-friendly:** Perfect for LLMs, CI pipelines, review bots, automation

---

## Installation

```bash
git clone https://github.com/YOURORG/langtools-mcp.git
cd langtools-mcp
uv pip install -e .
```

### Python/Ruff (current language supported)

- By default, Ruff is installed as a Python dependency and used from your environment.
- You *do not* need to install Node, gopls, or other tools unless you want analysis for non-Python languages.

---

## Quickstart

### Run the MCP server (daemon sidecar is automatic):

```bash
python -m langtools_mcp
```

To process a single file:
```bash
python -m langtools_mcp path/to/your_file.py
```

---

## Language Tool Installation/Usage Notes

- **Python (Ruff):**
    - Will run automatically if installed as a Python dep (by pip/uv/uvx).  
    - _**Gatekeeper on macOS:**_  
      If you ever install Ruff manually as a native binary (not via pip), you may need to allow it in System Settings > Privacy & Security. This is generally NOT necessary for pip/uv installs.

- **Go, Rust & Others:**
    - Future tool support will guide you to install/download the right linters if not already present on PATH.
    - Each tool’s onboarding will provide install guidance only as needed.

---

## How It Works

- MCP exposes an `AnalyzeFile` tool and protocol (see `src/langtools_mcp/server.py`) which dispatches analysis requests through a registry to the daemon.
- The daemon routes the request to the appropriate tool and returns normalized results as JSON.

---

## Daemon Management

- Daemon startup and shutdown is fully automated—no user action needed.
- You can check for a running daemon via:
  ```
  ps aux | grep '[p]ython.*langtools_mcp.langtools_daemon.main'
  ```

---

## Troubleshooting

- **Tool not found error:**  
  Make sure the language tool (e.g. Ruff for Python) is installed via pip/uv/uvx.
- **macOS Gatekeeper:**  
  Only an issue if you install a language tool manually as a system binary; not typical for default usage.

---

## Contributing

We welcome new language tool integrations, agent connectors, and usability improvements!  
Open a PR or issue, or see `CONTRIBUTING.md` for details.

---

## License

[MIT](LICENSE)

---

## Roadmap

- Add Go (gopls), Rust (rust-analyzer), TypeScript, shellcheck, etc.
- More advanced batch analysis/LLM feedback features
- CI/CD and automation scripts
- Ergonomic developer onboarding

---

**Questions?**  
Open an issue or discussion, or join our community chat!
