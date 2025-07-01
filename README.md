# lsp-mcp: Multi-Language Code Analyzer for LLMs

## Overview

**lsp-mcp** provides robust, multi-language **code analysis** and static checking tools, via a modular "sidecar" daemon architecture.  
It is designed to help Large Language Models (LLMs) or humans automatically lint, type-check, and improve code in Python—and, soon, other languages—with minimal installation friction and maximum transparency.

<a href="https://glama.ai/mcp/servers/@flothjl/lsp-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@flothjl/lsp-mcp/badge" alt="lsp-mcp MCP server" />
</a>

- ⚡ **Fast**: Leverages tools like [Ruff](https://github.com/astral-sh/ruff) for blazing-fast Python analysis.
- 🛡️ **Safe**: Daemon sidecar downloads and manages analysis tools, keeping your environment clean.
- 🖥️ **Extensible**: Built to plug in gopls, rust-analyzer, and others in future releases.

---

## Architecture

```text
+---------------------+      HTTP (localhost)       +----------------------------+
|   lsp-mcp (MCP)     |<-------------------------->|     LSP Daemon Sidecar      |
+---------------------+                             +----------------------------+
                                                       |   (runs linters/checkers)
                                                       v
                                                   ruff, gopls, ...
```

When you launch the MCP server or analyze a file, an LSP daemon is spun up as a subprocess and managed automatically.  
All language-analysis requests are brokered across this daemon boundary for platform safety and flexibility.

---

## Features

- **Analyze Python files for errors, warnings, and code quality with Ruff**
- Automatic subprocess management of the code analysis daemon
- Fully pip/uvx-installable; no Homebrew or manual download required (for Ruff)
- Friendly Mac and cross-platform onboarding (see Gatekeeper notes below)

---

## Installation

### 1. Clone and install dependencies

```bash
git clone https://github.com/YOURORG/lsp-mcp.git
cd lsp-mcp
uv pip install -e .       # Or: uvx pip install -e .
```

### 2. Confirm Ruff Is Available

`ruff` is listed as a dependency and should be installed automatically—no need to install Node or npm!

---

## Quickstart

### **Run MCP Analysis Server (Daemon will autostart):**

```bash
python -m lsp_mcp
```

### **Manual Analysis of a Python File:**

```bash
python -m lsp_mcp path/to/your_script.py
```
or
```bash
uvx run python -m lsp_mcp path/to/your_script.py
```

---

## Analyzing Code

- MCP exposes an `AnalyzeFile` tool (see `src/lsp_mcp/server.py`) which, when called, routes your request through the analyzer registry and daemon, then returns results as JSON.
- See the code in `lsp_mcp/lsp/ruff_analyzer.py` for integration example.

---

## Daemon Management

- The LSP daemon is managed for you:
    - **Startup:** MCP spawns it as a subprocess
    - **Shutdown:** On exit or Ctrl+C, MCP ensures the daemon is cleanly stopped
- (Advanced) To check the daemon:  
  `ps aux | grep '[p]ython.*lsp_mcp.lsp_daemon.main'`

---

## ⚠️ Mac Gatekeeper & ✅ Security Notes

- The Ruff binary (when installed via pip/uvx from PyPI) is trusted and should "just work."
- If you ever override the Ruff binary by downloading it yourself (not typical), you may see:
    > "ruff" cannot be opened because Apple cannot check it for malicious software.
- _If this happens_:  
    Go to **System Settings → Privacy & Security** and click **Allow Anyway** for Ruff.
- For extra safety, check the Ruff binary's checksums or install via PyPI/Homebrew.

---

## Troubleshooting

- **Ruff not found error:**  
  Make sure you installed with `pip install ruff` or `uvx pip install -e .`
- **Daemon not starting:**  
  Ensure your environment allows subprocesses and no port conflicts exist.
- **Gatekeeper (macOS):**  
  See "Mac Gatekeeper & Security" above.

---

## Contributing

PRs and feature requests welcome!  
See `CONTRIBUTING.md` for development workflow, or open an issue with your suggestions.

---

## License

[MIT](LICENSE)

---

## Roadmap

- Add analyzers/daemons for Go (gopls), Rust (rust-analyzer), and others
- Cross-platform binary download/bootstrapping
- More advanced LSP-mode analysis features

---

## Questions?  
Open an issue or discussion, or join our community chat!