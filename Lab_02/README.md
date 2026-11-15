# Order Data Processor (Variant 7)

Laboratory project for the course **"Professional Python"** (Laboratory Work No. 2, Variant 7 — aligned with Laboratory Work No. 1).

## Description

Module for processing structured online store order data demonstrating professional usage of built-in and specialized Python data structures (`list`, `tuple`, `set`, `dict`, `collections.Counter`, `collections.defaultdict`, `collections.deque`), comprehensions (`list`, `set`, `dict`), generator expressions, functional decomposition, `*args`, `**kwargs`, `lambda` functions, closures, decorators (`@measure_time`, `@log_call`, `@repeat`), pipeline processing, and algorithmic time-complexity benchmarking ($O(n)$ vs $O(1)$ on 1,000 / 10,000 / 100,000 records).

## Requirements

- Python 3.11+

## Installation

```bash
python -m venv .venv
```

Activate the virtual environment:

- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- **Windows (CMD):**
  ```cmd
  .venv\Scripts\activate
  ```
- **Linux / macOS:**
  ```bash
  source .venv/bin/activate
  ```

Install the package in editable mode:

```bash
python -m pip install -e .
```

## Run

Run as a Python module (full demo report + interactive CLI menu):

```bash
python -m data_processor.main
```

Run in non-interactive demo mode only (including the 1,000 / 10,000 / 100,000 benchmark):

```bash
python -m data_processor.main --demo
```

Or run via the registered console script:

```bash
data-processor
```

## Run Tests

```bash
pytest
```

## Project Structure

```text
Lab_02/
├── report/
│   ├── README.md
│   └── Lab_02_Report.docx
├── src/
│   └── data_processor/
│       ├── __init__.py
│       ├── data.py
│       ├── decorators.py
│       ├── processors.py
│       ├── analytics.py
│       └── main.py
├── tests/
│   └── test_data_processor.py
├── .gitignore
├── README.md
└── pyproject.toml
```

## Author

- **Student:** Назар Поцелуйко
- **Variant:** №7

