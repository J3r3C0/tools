# Sheratan Version Reconciler

A Python CLI tool for comparing, analyzing, and merging multiple Sheratan installations into a unified version.

## Features

✨ **Multi-Version Comparison**
- Compare file structures across multiple Sheratan installations
- Detect missing, extra, and modified files
- Calculate similarity scores between versions

🔍 **Deep Code Analysis**
- AST-based Python code comparison
- Detect function/class additions and removals
- Identify import statement changes
- Classify changes by severity

⚙️ **Configuration Drift Detection**
- Parse YAML, JSON, INI, and .env files
- Identify configuration conflicts
- Highlight security-sensitive settings

🔀 **Intelligent Merging**
- Multiple merge strategies (newest, manual, rules-based)
- Automatic conflict resolution
- Backup original installations
- Union merge for dependencies

📊 **Comprehensive Reporting**
- Generate reports in Markdown, JSON, or HTML
- Detailed diff analysis
- Visual similarity matrices

## Installation

```bash
# Clone or navigate to the project directory
cd sheratan-reconciler

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### 1. Scan Multiple Versions

```bash
python -m src.main scan C:\sheratan_v1 C:\sheratan_v2 C:\sheratan_v3
```

### 2. Generate Comparison Report

```bash
python -m src.main compare C:\sheratan_v1 C:\sheratan_v2 -o comparison_report.md
```

### 3. Merge Versions (Dry Run)

```bash
python -m src.main merge C:\sheratan_v1 C:\sheratan_v2 --dry-run
```

### 4. Merge Versions (Actual)

```bash
python -m src.main merge C:\sheratan_v1 C:\sheratan_v2 -o C:\sheratan_unified
```

## Usage

### Commands

#### `scan`
Scan and analyze multiple Sheratan directories.

```bash
python -m src.main scan [DIRECTORIES...] [OPTIONS]

Options:
  -c, --config PATH  Path to configuration file
```

#### `compare`
Generate detailed comparison report.

```bash
python -m src.main compare [DIRECTORIES...] [OPTIONS]

Options:
  -o, --output PATH  Output file path (default: sheratan_comparison_report.md)
  -f, --format TEXT  Report format: markdown, json, html (default: markdown)
  -c, --config PATH  Path to configuration file
```

#### `merge`
Merge multiple versions into unified installation.

```bash
python -m src.main merge [DIRECTORIES...] [OPTIONS]

Options:
  -o, --output PATH  Output directory for merged version
  --dry-run          Perform dry run without making changes
  -c, --config PATH  Path to configuration file
```

#### `report`
Export analysis in multiple formats.

```bash
python -m src.main report [DIRECTORIES...] [OPTIONS]

Options:
  -c, --config PATH  Path to configuration file
```

## Configuration

Create a `config.yaml` file to customize behavior:

```yaml
# Merge strategy: newest, manual, rules
merge_strategy: newest

# Backup original directories
backup_originals: true

# Output directory
output_directory: ./sheratan-unified

# Ignore patterns (gitignore-style)
ignore_patterns:
  - "*.pyc"
  - "__pycache__"
  - ".git"
  - "*.log"
  - "venv/"

# Critical files that must exist
critical_files:
  - "core.py"
  - "orchestrator.py"
  - "config.py"

# Reporting options
reporting:
  format: markdown
  include_diffs: true
  max_diff_lines: 100
```

## Advanced Usage

### Custom Merge Rules

Create `config/rules.yaml` to define file-specific merge strategies:

```yaml
file_priorities:
  "*.py": newest_with_most_functions
  "*.yaml": merge_keys
  ".env": manual_review
  "requirements.txt": union_of_all
```

### Programmatic Usage

```python
from pathlib import Path
from src.app import SheratanReconciler

# Initialize reconciler
reconciler = SheratanReconciler(config_path=Path('config/config.yaml'))

# Define directories
directories = {
    'version_1': Path('C:/sheratan_v1'),
    'version_2': Path('C:/sheratan_v2')
}

# Scan and analyze
results = reconciler.scan(directories)

# Generate report
reconciler.compare(directories, output_path=Path('report.md'))

# Merge versions
reconciler.merge(directories, output_dir=Path('unified'))
```

## Project Structure

```
sheratan-reconciler/
├── src/
│   ├── main.py              # CLI entry point
│   ├── app.py               # Core application logic
│   ├── analyzers/
│   │   ├── file_structure.py    # File tree comparison
│   │   ├── code_diff.py         # Code-level diff analysis
│   │   └── config_drift.py      # Configuration comparison
│   ├── reconciler/
│   │   ├── merger.py            # Merge logic
│   │   └── conflict_resolver.py # Conflict resolution
│   └── utils/
│       ├── file_ops.py          # File operations
│       └── reporter.py          # Report generation
├── tests/                   # Unit and integration tests
├── config/                  # Configuration files
├── docs/                    # Documentation
└── requirements.txt         # Dependencies
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_analyzers.py -v
```

## Examples

### Example 1: Compare Two Versions

```bash
python -m src.main compare C:\sauber_main C:\sheratan_backup -o comparison.md
```

### Example 2: Merge Three Versions

```bash
python -m src.main merge C:\sheratan_v1 C:\sheratan_v2 C:\sheratan_v3 -o C:\sheratan_final
```

### Example 3: Scan with Custom Config

```bash
python -m src.main scan C:\sheratan_* -c custom_config.yaml
```

## Troubleshooting

**Issue**: "No valid directories found"
- **Solution**: Ensure directory paths exist and are accessible

**Issue**: Merge conflicts not resolving
- **Solution**: Use `--dry-run` first to preview changes, then use manual resolution mode

**Issue**: Missing dependencies
- **Solution**: Run `pip install -r requirements.txt`

## Contributing

Contributions welcome! Please ensure:
- All tests pass (`pytest tests/`)
- Code follows PEP 8 style guidelines
- New features include tests

## License

MIT License - See LICENSE file for details

## Support

For issues or questions, please open an issue on the project repository.
