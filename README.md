# langtools-mcp

> [!WARNING]
> 🚧 This is actively being developed, so expect issues. Currently focusing on compatibility with the on-machine AI agent [Goose](https://block.github.io/goose/docs/quickstart/). 🚧

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**langtools-mcp** is a Model Context Protocol (MCP) server and client toolkit that gives LLMs and AI agents unified access to real static analysis tools—including batch CLI checkers (like Ruff and go vet) and LSPs (like gopls, rust-analyzer, and more).

We've all been there:

- LLM writes code that doesn't compile due to hallucinating standard libraries that don't exist, syntax errors, etc.
- LLM writes functional code, but the style, formatting, and linting is non-existent (I'm looking at you, unused imports)

**langtools-mcp** aims to help solve this by letting your AI and agentic apps **catch, explain, and even fix** issues in code, by calling the same tools expert programmers use. The goal is simply for this MCP to be a tool that the LLM begins using as part of its dev cycle. Just like IDEs and LSPs supercharged humans' ability to quickly assess and fix issues during the dev process, langtools aims to do this with an MCP tool.

- 🧠 **Supercharge Agents:** Let your LLMs/AI validate, lint, and debug their own code.
- 🧩 **Modular & Extensible:** Add new languages/tools in minutes via strategies.
- ⚡ **Daemon or Batch:** Runs as a fast HTTP daemon for LSP and batch CLI tools.

---

## Quickstart

### Configuring for Project [Goose](https://block.github.io/goose/docs/quickstart/)

```yaml
langtools:
  args:
    - --from
    - https://github.com/flothjl/langtools-mcp
    - langtools-mcp
  bundled: null
  cmd: uvx
  description: null
  enabled: true
  env_keys: []
  envs: {}
  name: langtools-mcp
  timeout: null
  type: stdio
```

<p align="center">
<img src="./assets/goose_sample.png" style="width: 75%;">
</p>

#### Configuration Options

```bash
export LANGTOOLS_PYTHON_TOOLS='["ruff"]'
export LANGTOOLS_GO_GO_TOOLS='["vet"]'
```

| Language | Tools         |
| -------- | ------------- |
| Python   | ruff, pyright |
| Go       | vet           |

---

## Installation

```bash
git clone https://github.com/flothjl/langtools-mcp.git
cd langtools-mcp
uv sync  # or pip install -e .[dev]
```

**Requirements:** Python 3.10+, plus [ruff](https://docs.astral.sh/ruff/), [pyright](https://github.com/microsoft/pyright), and [Go](https://go.dev/doc/install) for Go support (must be in your PATH).

---

## Roadmap & Supported Tools

- [x] **Python**: Ruff, Pyright (CLI)
- [x] **Go**: go vet (CLI)
- [ ] **Rust**: rust-analyzer (LSP)
- [ ] **JavaScript/TypeScript**: tsc, eslint (planned)

Want to add support for your favorite tool or language?
Open a [PR](https://github.com/flothjl/langtools-mcp/pulls) or start a [Discussion](https://github.com/flothjl/langtools-mcp/discussions)!

---

## Contributing

- Fork, clone, and submit a PR!
- Code and docs welcome for new languages, better error messages, and more.
