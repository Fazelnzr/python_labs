# Order Manager (Variant 7)

Laboratory project for the course **"Professional Python"** (Laboratory Work No. 1, Variant 7).

## Description

Console application for managing online store orders, validating order data, tracking order statuses (`new`, `paid`, `shipped`, `cancelled`), applying automatic volume discounts, and calculating financial statistics.

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

Run as a Python module (interactive CLI with initial demo output):

```bash
python -m order_manager.main
```

Run in non-interactive demo mode only:

```bash
python -m order_manager.main --demo
```

Or run via the registered console script:

```bash
order-manager
```

## Run Tests

```bash
pytest
```

## Project Structure

```text
Lab_1/
├── report/
│   ├── README.md
│   └── Lab_01_Report_Variant_07.docx
├── src/
│   └── order_manager/
│       ├── __init__.py
│       ├── exceptions.py
│       ├── models.py
│       ├── services.py
│       └── main.py
├── tests/
│   └── test_services.py
├── .gitignore
├── README.md
└── pyproject.toml
```

## Author

- **Student:** Назар Поцелуйко
- **Variant:** №7
