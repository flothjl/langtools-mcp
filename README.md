# langtools-mcp

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/flothjl/langtools-mcp) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

An MCP Server that gives LLMs and AI agents the power to read, analyze, and fix code.

**langtools-mcp** provides a single, unified API for best-in-class linters and language servers (like Ruff, gopls, and rust-analyzer), enabling any application to perform complex static analysis with a simple request.

---

## Why langtools-mcp?

Code-generating LLMs often make subtle mistakes. `langtools-mcp` acts as an automated code reviewer, allowing agents to **self-correct** and improve their output.

- ✅ **Unified API:** One simple entrypoint for a growing suite of diverse language tools.
- 🧠 **Supercharge Agents:** Give your AI the ability to validate code, understand errors, and learn from feedback.
- 🧩 **Modular & Extensible:** Easily add support for new languages and tools without changing your core application.
- ⚙️ **Headless & Scalable:** Built as a lightweight sidecar, it's perfect for CI pipelines, automated code review bots, and multi-language repositories.

---

## Architecture

`langtools-mcp` runs a central daemon (`langtools_daemon`) that manages all language tools. Your application communicates with the daemon via a simple client, ensuring that analysis is fast, efficient, and decoupled from your main process.

````text
+-----------------------------------+      Simple HTTP     +-----------------------------------+
|                                   | <------------------->|                                   |
|  Your Application / AI Agent      |                      |     langtools-mcp Daemon          |
|  (Uses langtools_mcp client)      |                      |   (Manages & runs language tools) |
|                                   |                      |                                   |
+-----------------------------------+                      +-----------------------------------+
                                                                           |
                                                                  (Dispatches to...)
                                                                           v
                                                         +------+   +-------+   +----------------+
                                                         | Ruff | , | gopls | , | rust-analyzer  | ...
                                                         +------+   +-------+   +----------------+

## Installation

```bash
git clone https://github.com/flothjl/langtools-mcp.git
cd langtools-mcp
uv sync
````

---

## Quickstart

To process a single file:

```bash
python -m langtools_mcp path/to/your_file.py
```

---

## How It Works

1. The langtools-mcp client identifies the file type and sends an analysis request to the daemon.
2. The daemon maintains a registry of available language tools and routes the request to the appropriate one (e.g., .py -> ruff).
3. The tool runs and returns its raw output.
4. The daemon normalizes the results into a consistent JSON format and sends it back to the client.

---

## Roadmap

[x] Python (via Ruff)

[x] Go (via gopls)

[ ] Rust (via rust-analyzer)

[ ] TypeScript/JavaScript (via tsc)

---

**Questions?**  
Open an issue or discussion, or join our community chat!
