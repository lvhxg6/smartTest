# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Smart Dev Mantis is an LLM-driven API automated testing platform that uses Claude Code CLI to generate, execute, and self-heal test cases. It transforms traditional manual testing into an AI-powered workflow: **User Input -> AI Generate -> AI Execute -> AI Self-Heal**.

## Common Commands

```bash
# Start Web UI (primary interface)
python run_web.py
python run_web.py --port 8080 --debug

# CLI mode - Light mode (Swagger only)
python -m src.main --swagger api.json --base-url https://api.example.com

# CLI mode - Full mode (with business rules)
python -m src.main --swagger api.json --base-url https://api.example.com \
    --requirements rules.md --data data.md --token "Bearer xxx"

# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Four-Phase Workflow Engine

The core workflow in `src/core/workflow_engine.py` orchestrates four phases:

1. **Planning** - Analyzes Swagger + business rules, generates `testcases.md`
2. **Generating** - Creates Pytest code from test case design
3. **Executing + Healing** - Runs tests with automatic syntax/logic self-healing
4. **Finalizing** - Produces business reports and bug lists

### Core Module Responsibilities

| Module | Location | Purpose |
|--------|----------|---------|
| `WorkflowEngine` | `src/core/workflow_engine.py` | Orchestrates 4-phase workflow |
| `CLIAdapter` | `src/core/cli_adapter.py` | Wraps Claude Code CLI calls |
| `PromptBuilder` | `src/core/prompt_builder.py` | Loads and fills prompt templates |
| `PytestRunner` | `src/core/pytest_runner.py` | Executes pytest, parses results |
| `ResultJudge` | `src/core/result_judge.py` | Decides healing type (syntax/logic) |
| `DependencyAnalyzer` | `src/core/dependency_analyzer.py` | Static API dependency analysis |
| `LoadTestRunner` | `src/core/load_test_runner.py` | Load testing with Locust |

### Data Flow

```
InputParser -> TaskContext -> WorkflowEngine -> FinalReport
                                   |
                    CLISession (maintains Claude context)
                                   |
              [plan_prompt -> generate_prompt -> heal_prompts]
```

### Key Data Models (`src/models/`)

- `TaskContext` - Central data container for the workflow
- `TestCaseResult` - Individual test execution result
- `FinalReport` - Final output with statistics and file paths
- `ErrorInfo` - Structured error information for healing decisions

### Prompt Templates (`src/templates/`)

- `plan_prompt.txt` - Test case design generation
- `generate_prompt.txt` - Pytest code generation
- `heal_syntax_prompt.txt` - Syntax error repair
- `heal_logic_prompt.txt` - Logic error analysis (Bug vs script issue)
- `load_test_prompt.txt` - Load test script generation

### Self-Healing Logic

The `ResultJudge` determines healing type:
- **SYNTAX** errors (SyntaxError, NameError, ImportError) -> Code repair
- **ASSERTION** failures in full mode (with business rules) -> Bug determination
- **CONNECTION** errors -> No healing (environment issue)

### Output Structure

Each execution creates a timestamped directory under `output/`:
```
output/YYYY-MM-DD_HHMMSS/
├── testcases.md           # Test case design document
├── tests/                 # Generated Pytest files
│   ├── conftest.py
│   └── test_*.py
├── reports/
│   ├── report.html        # Pytest HTML report
│   └── results.xml        # JUnit XML
├── dependency_analysis.json
├── bug_report.json
└── business_report.html
```

### Web UI

Flask + Flask-SocketIO application in `src/web/`:
- Real-time log streaming via WebSocket
- Todo progress display during execution
- Supports cancel operations

### CLI Adapter Details

The adapter calls Claude Code CLI with:
```bash
claude -p --output-format stream-json --verbose \
  --dangerously-skip-permissions \
  --allowedTools Read,Write,Edit,Bash,Glob,Grep \
  [--resume sessionId]
```

Session mode maintains context across phases (planning -> generating -> healing).

## Test Modes

- **Light Mode**: Only Swagger provided, assertion failures marked as bugs directly
- **Full Mode**: Swagger + business rules, assertion failures trigger logic healing to determine if bug or script issue
