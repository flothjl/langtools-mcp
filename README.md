# langtools-mcp

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**langtools-mcp** is a Model Context Protocol (MCP) server and client toolkit that gives LLMs and AI agents unified access to real static analysis tools—including batch CLI checkers (like Ruff and go vet) and LSPs (like gopls, rust-analyzer, and more).

---

## Why langtools-mcp?

Large Language Models often write code that _runs_ but doesn’t follow best practices, or contains subtle bugs. **langtools-mcp** lets your AI and agentic apps **catch, explain, and even fix** issues in code, by calling the same tools expert programmers use.

- ✅ **Unified API:** One entrypoint for Python, Go, and more—CLI or LSP tools, same API.
- 🧠 **Supercharge Agents:** Let your LLMs/AI validate, lint, and debug their own code.
- 🧩 **Modular & Extensible:** Add new languages/tools in minutes via Python strategies.
- ⚡ **Daemon or Batch:** Runs as a fast HTTP daemon for LSP and batch CLI tools.
- 🏗️ **Perfect for:**

  - Automated code review bots
  - Multi-language repositories
  - LLM self-correction workflows
  - Continuous Integration (CI) pipelines

---

## Architecture

`langtools-mcp` launches a **central daemon** (`langtools_daemon`) that manages language tools for each supported language.
Your app or agent communicates with the daemon via a simple HTTP interface (local), using the provided Python client.

```
+----------------------------+          HTTP API        +--------------------------+
|                            | <----------------------> |                          |
|   Your App / LLM / Agent   |                          |  langtools-mcp Daemon    |
|   (Uses langtools_mcp)     |                          | (Manages code analysis)  |
+----------------------------+                          +--------------------------+
                                                                    |
                                                          +----------+----------+
                                                          |  Ruff, go vet, ...  |
                                                          |  (CLI or LSP)       |
                                                          +---------------------+
```

- **CLI tools** are executed as needed—stateless, fast.
- **LSPs** (if configured) are pooled and reused for performance.

---

## Installation

```bash
git clone https://github.com/flothjl/langtools-mcp.git
cd langtools-mcp
uv sync  # or pip install -e .[dev]
```

**Requirements:** Python 3.10+, plus [ruff](https://docs.astral.sh/ruff/), [pyright](https://github.com/microsoft/pyright), and [Go](https://go.dev/doc/install) for Go support (must be in your PATH).

---

## Quickstart

Analyze a Python or Go project:

```bash
python -m langtools_mcp path/to/your_file.py
```

Or, use the daemon in your own code:

```python
from langtools_mcp.langtools.analysis import run_analysis_for_language

result = run_analysis_for_language("python", "/path/to/my/project")
print(result)
```

---

## HTTP API Example

The daemon exposes a simple HTTP API (default: `localhost:61782`):

### Request

```json
POST /
{
  "language": "python",
  "project_root": "/absolute/path/to/project"
}
```

### Response

```json
{
  "status": "ok",
  "diagnostics": [
    {
      "source": "ruff",
      "output": [ ... ]
    },
    {
      "source": "pyright",
      "output": [ ... ]
    }
  ]
}
```

---

## Roadmap & Supported Tools

- [x] **Python**: Ruff, Pyright (CLI)
- [x] **Go**: go vet (CLI)
- [ ] **Go**: gopls (LSP; hybrid mode coming)
- [ ] **Rust**: rust-analyzer (LSP)
- [ ] **JavaScript/TypeScript**: tsc, eslint (planned)

Want to add support for your favorite tool or language?
Open a [PR](https://github.com/flothjl/langtools-mcp/pulls) or start a [Discussion](https://github.com/flothjl/langtools-mcp/discussions)!

---

## FAQ

**Q: Do I need to run a daemon for CLI-only tools?**
_A: The daemon makes it easier to integrate with LLMs and lets you mix in LSPs or future batch tools seamlessly. For simple batch runs, you can call the CLI client directly._

**Q: What if a language only supports LSP, not CLI?**
_A: langtools-mcp’s architecture supports both. Each strategy decides whether to use a CLI or LSP process under the hood._

---

## Contributing

- Fork, clone, and submit a PR!
- Code and docs welcome for new languages, better error messages, and more.

---

**Questions?**
Open an [issue](https://github.com/flothjl/langtools-mcp/issues), or join our community chat!
