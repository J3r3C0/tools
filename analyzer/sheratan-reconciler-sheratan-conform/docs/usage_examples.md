# Usage Examples

## Example 1: Basic Comparison

Compare two Sheratan installations and generate a report:

```bash
python -m src.main compare C:\sheratan_main C:\sheratan_backup
```

**Output**: `sheratan_comparison_report.md`

## Example 2: Scan Multiple Versions

Scan three versions and view summary:

```bash
python -m src.main scan C:\sheratan_v1 C:\sheratan_v2 C:\sheratan_v3
```

**Console Output**:
```
Scanning 3 Sheratan versions...
  ✓ sheratan_v1: C:\sheratan_v1
  ✓ sheratan_v2: C:\sheratan_v2
  ✓ sheratan_v3: C:\sheratan_v3

Analyzing file structures...
Analyzing code differences...
Analyzing configuration drift...

Sheratan Version Comparison Summary:
  Versions: 3
  Total Files: 245
  Different Files: 12
  Conflicts: 3

✓ Scan complete!
```

## Example 3: Dry Run Merge

Preview merge without making changes:

```bash
python -m src.main merge C:\sheratan_v1 C:\sheratan_v2 --dry-run
```

## Example 4: Actual Merge

Merge two versions into unified installation:

```bash
python -m src.main merge C:\sheratan_v1 C:\sheratan_v2 -o C:\sheratan_unified
```

**Workflow**:
1. Analyzes both versions
2. Shows merge summary
3. Asks for confirmation
4. Creates backups
5. Merges files
6. Generates summary report

## Example 5: Custom Configuration

Use custom configuration file:

```bash
python -m src.main merge C:\sheratan_v1 C:\sheratan_v2 -c my_config.yaml
```

**my_config.yaml**:
```yaml
merge_strategy: manual
backup_originals: true
output_directory: ./unified
ignore_patterns:
  - "*.pyc"
  - "venv/"
```

## Example 6: Generate Multiple Report Formats

Export analysis in all formats:

```bash
python -m src.main report C:\sheratan_v1 C:\sheratan_v2
```

**Generates**:
- `sheratan_report.markdown`
- `sheratan_report.json`
- `sheratan_report.html`

## Example 7: Programmatic Usage

Use as Python library:

```python
from pathlib import Path
from src.app import SheratanReconciler

# Initialize
reconciler = SheratanReconciler()

# Define versions
dirs = {
    'main': Path('C:/sheratan_main'),
    'backup': Path('C:/sheratan_backup')
}

# Scan
results = reconciler.scan(dirs)
print(f"Found {results['summary']['different_files']} different files")

# Merge
reconciler.merge(dirs, output_dir=Path('C:/unified'))
```

## Example 8: Comparing Specific Sheratan Installations

Compare your actual Sheratan installations:

```bash
# If you have sauber_main and other Sheratan versions
python -m src.main compare C:\sauber_main C:\sheratan_backup -o sheratan_analysis.md
```

## Example 9: Merging with Manual Conflict Resolution

For critical merges where you want to review each conflict:

1. Create custom rules file:

**config/custom_rules.yaml**:
```yaml
file_priorities:
  "core.py": manual_review
  "orchestrator.py": manual_review
  "*.yaml": manual_review
```

2. Run merge:
```bash
python -m src.main merge C:\sheratan_v1 C:\sheratan_v2 -c config/custom_rules.yaml
```

3. Tool will prompt for each conflict:
```
Conflict detected for: core.py
Available versions:
  1. sheratan_v1 (size: 15234 bytes, modified: 1705849200)
  2. sheratan_v2 (size: 15890 bytes, modified: 1705935600)
Select version [1]: 2
```

## Example 10: Analyzing Only Configuration Drift

Focus on configuration differences:

```python
from pathlib import Path
from src.app import SheratanReconciler

reconciler = SheratanReconciler()

dirs = {
    'v1': Path('C:/sheratan_v1'),
    'v2': Path('C:/sheratan_v2')
}

results = reconciler.scan(dirs)
config_drift = results['config_drift']

print(f"Configuration conflicts: {config_drift['conflict_count']}")
for conflict in config_drift['conflicts']:
    print(f"  {conflict['file']}: {conflict['description']}")
```

## Tips and Best Practices

### Before Merging

1. **Always run scan first**:
   ```bash
   python -m src.main scan [dirs...]
   ```

2. **Generate comparison report**:
   ```bash
   python -m src.main compare [dirs...] -o report.md
   ```

3. **Review the report** to understand differences

4. **Run dry-run merge**:
   ```bash
   python -m src.main merge [dirs...] --dry-run
   ```

### During Merge

1. **Keep backups enabled** (default)
2. **Review conflicts carefully** in manual mode
3. **Check critical files** (core.py, config.py, etc.)

### After Merge

1. **Verify unified version** works correctly
2. **Run tests** if available
3. **Keep backups** until verified
4. **Document changes** made during merge
