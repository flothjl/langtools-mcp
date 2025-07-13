# Gopls Configuration Support

## Overview

The `GoplsLSPAdapter` now supports configuring gopls with the same settings used in popular editors like LazyVim, VSCode, and others. This allows fine-tuning of Go language analysis, formatting, and diagnostic behavior.

## Features

### 1. Default Configuration (LazyVim-style)

The adapter comes with sensible defaults similar to LazyVim's configuration:

```python
default_config = {
    "gofumpt": True,
    "codelenses": {
        "gc_details": False,
        "generate": True,
        "regenerate_cgo": True,
        "run_govulncheck": True,
        "test": True,
        "tidy": True,
        "upgrade_dependency": True,
        "vendor": True,
    },
    "hints": {
        "assignVariableTypes": True,
        "compositeLiteralFields": True,
        "compositeLiteralTypes": True,
        "constantValues": True,
        "functionTypeParameters": True,
        "parameterNames": True,
        "rangeVariableTypes": True,
    },
    "analyses": {
        "nilness": True,
        "unusedparams": True,
        "unusedwrite": True,
        "useany": True,
    },
    "usePlaceholders": True,
    "completeUnimported": True,
    "staticcheck": True,
    "directoryFilters": [
        "-.git", "-.vscode", "-.idea", "-.vscode-test", "-node_modules"
    ],
    "semanticTokens": True,
}
```

### 2. Custom Configuration

You can provide custom configuration when creating the adapter:

```python
custom_config = {
    "staticcheck": True,
    "analyses": {
        "unusedparams": True,
        "nilness": True,
        "shadow": True,
    },
    "gofumpt": True,
}

adapter = GoplsLSPAdapter(
    root_path="/path/to/project",
    config=custom_config
)
```

### 3. Configuration Categories

#### Analysis Settings
Control which static analysis checks are enabled:
- `unusedparams`: Detect unused function parameters
- `unusedwrite`: Detect unused variable assignments
- `nilness`: Detect potential nil pointer dereferences
- `useany`: Suggest using 'any' instead of 'interface{}'
- `shadow`: Detect variable shadowing
- `printf`: Check printf-style format strings

#### Formatting Settings
- `gofumpt`: Use gofumpt for stricter formatting
- `staticcheck`: Enable staticcheck analysis

#### Code Features
- `completeUnimported`: Auto-complete unimported packages
- `usePlaceholders`: Use placeholders in completions
- `semanticTokens`: Enable semantic token highlighting

#### Code Lenses
Configure which code lenses (actionable overlays) are shown:
- `generate`: Show "go generate" commands
- `test`: Show test run options
- `tidy`: Show "go mod tidy" options
- `run_govulncheck`: Show vulnerability checking

## Usage Examples

### Basic Usage with Default Config
```python
from langtools_mcp.langtools_daemon.gopls_lsp_adapter import GoplsLSPAdapter

# Uses default LazyVim-style configuration
adapter = GoplsLSPAdapter(root_path="/path/to/go/project")
result = adapter.analyze("main.go")
```

### Minimal Configuration
```python
minimal_config = {
    "staticcheck": True,
    "analyses": {
        "unusedparams": True,
    }
}

adapter = GoplsLSPAdapter(
    root_path="/path/to/go/project",
    config=minimal_config
)
```

### Development-focused Configuration
```python
dev_config = {
    "staticcheck": True,
    "gofumpt": True,
    "analyses": {
        "unusedparams": True,
        "unusedwrite": True,
        "nilness": True,
        "shadow": True,
    },
    "codelenses": {
        "test": True,
        "generate": True,
    },
    "hints": {
        "parameterNames": True,
        "assignVariableTypes": True,
    }
}

adapter = GoplsLSPAdapter(
    root_path="/path/to/go/project", 
    config=dev_config
)
```

## Configuration Transmission

The adapter sends configuration to gopls via two methods:

1. **Initialization Options** (during LSP initialization):
```json
{
  "initializationOptions": {
    "settings": {
      "gopls": { /* your config */ }
    }
  }
}
```

2. **Workspace Configuration** (after initialization):
```json
{
  "method": "workspace/didChangeConfiguration",
  "params": {
    "settings": {
      "gopls": { /* your config */ }
    }
  }
}
```

This dual approach ensures maximum compatibility with different gopls versions.

## Diagnostic Sources

With proper configuration, you'll see diagnostics from multiple sources:
- `compiler`: Go compiler errors and warnings
- `unusedparams`: Unused parameter analysis
- `staticcheck`: Staticcheck tool analysis
- `nilness`: Nil pointer analysis
- `shadow`: Variable shadowing detection

## Testing Configuration

The adapter includes comprehensive tests to verify configuration functionality:

```bash
# Run gopls configuration tests
pytest tests/test_lsp_adapter.py::test_gopls_configuration -v
```

## Integration with Other Tools

The configuration is compatible with:
- **LazyVim**: Uses the same configuration structure
- **VSCode Go extension**: Most settings map directly
- **Vim/Neovim LSP**: Standard LSP configuration
- **Emacs lsp-mode**: Compatible configuration format

## Performance Considerations

- **Staticcheck**: Adds comprehensive analysis but may increase analysis time
- **Multiple Analyses**: Each enabled analysis adds processing overhead
- **Code Lenses**: Visual features that don't impact analysis performance
- **Hints**: Minimal performance impact, mainly for editor display

## Future Enhancements

Potential improvements:
- **Language-specific profiles**: Different configs for different project types
- **Dynamic configuration**: Runtime configuration updates
- **Performance monitoring**: Track analysis timing with different configs
- **Configuration validation**: Validate config against gopls capabilities