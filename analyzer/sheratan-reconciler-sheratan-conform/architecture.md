# Sheratan Version Reconciler - Architecture

## Overview

The Sheratan Version Reconciler is designed to compare, analyze, and merge multiple Sheratan installations into a unified version. The architecture follows a modular design with clear separation of concerns.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                            │
│                       (main.py)                              │
│  Commands: scan | compare | merge | report                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                   Application Layer                          │
│                      (app.py)                                │
│  SheratanReconciler - Orchestrates all operations           │
└─────┬───────────────┬──────────────┬────────────────────────┘
      │               │              │
┌─────▼─────┐  ┌─────▼─────┐  ┌────▼──────┐
│ Analyzers │  │Reconciler │  │ Utilities │
└───────────┘  └───────────┘  └───────────┘
      │               │              │
      ├─ FileStructure├─ Merger     ├─ FileOps
      ├─ CodeDiff     ├─ Conflict   └─ Reporter
      └─ ConfigDrift  │   Resolver
                      │
```

## Core Components

### 1. CLI Layer (`main.py`)

**Responsibility**: User interface and command routing

**Commands**:
- `scan` - Analyze multiple directories
- `compare` - Generate comparison reports
- `merge` - Merge versions into unified installation
- `report` - Export analysis in multiple formats

### 2. Application Layer (`app.py`)

**Class**: `SheratanReconciler`

**Responsibility**: Orchestrate all operations and coordinate between components

**Key Methods**:
- `scan()` - Perform comprehensive analysis
- `compare()` - Generate comparison reports
- `merge()` - Execute merge operations
- `report()` - Export results

### 3. Analyzer Components

#### FileStructureAnalyzer (`analyzers/file_structure.py`)

**Purpose**: Compare directory structures

**Features**:
- Build file trees for each version
- Identify common/unique/missing files
- Calculate similarity scores
- Generate structural statistics

#### CodeDiffAnalyzer (`analyzers/code_diff.py`)

**Purpose**: Analyze code-level differences

**Features**:
- AST-based semantic comparison
- Line-by-line diff generation
- Function/class change detection
- Import statement analysis
- Severity assessment

#### ConfigDriftAnalyzer (`analyzers/config_drift.py`)

**Purpose**: Compare configuration files

**Features**:
- Multi-format parsing (YAML, JSON, INI, .env)
- Nested configuration flattening
- Conflict detection
- Security-sensitive key identification

### 4. Reconciler Components

#### Merger (`reconciler/merger.py`)

**Purpose**: Combine multiple versions

**Features**:
- File-by-file merge logic
- Backup creation
- Union merge for dependencies
- Detailed merge logging

#### ConflictResolver (`reconciler/conflict_resolver.py`)

**Purpose**: Resolve conflicts during merge

**Strategies**:
- Newest (timestamp-based)
- Largest (size-based)
- Manual (interactive prompts)
- Rules-based (from configuration)

### 5. Utility Components

#### FileOperations (`utils/file_ops.py`)

**Purpose**: Safe file operations

**Features**:
- Directory walking with ignore patterns
- File hashing (SHA256)
- Safe copying with backups
- Metadata extraction

#### Reporter (`utils/reporter.py`)

**Purpose**: Generate reports

**Formats**:
- Markdown (human-readable)
- JSON (machine-readable)
- HTML (web-viewable)

## Data Flow

### Scan Operation

```
1. User provides directory paths
2. CLI parses arguments
3. SheratanReconciler initializes components
4. FileStructureAnalyzer builds file trees
5. CodeDiffAnalyzer compares Python files
6. ConfigDriftAnalyzer compares config files
7. Reporter generates summary
8. Results returned to user
```

### Merge Operation

```
1. User provides directories + output path
2. Scan operation performed first
3. User confirms merge
4. Merger creates backups (if enabled)
5. For each file:
   a. Check for conflicts
   b. Resolve using ConflictResolver
   c. Copy to output directory
6. Merge requirements.txt (union)
7. Generate merge summary
8. Return results
```

## Configuration System

### Config Files

1. **config.yaml** - Main configuration
   - Merge strategies
   - Ignore patterns
   - Output settings

2. **rules.yaml** - Merge rules
   - File-specific strategies
   - Directory priorities
   - Conflict resolution rules

### Configuration Loading

```
1. Check for user-provided config path
2. Load and parse YAML
3. Merge with default configuration
4. Apply to all components
```

## Extension Points

### Adding New Analyzers

1. Create new class in `src/analyzers/`
2. Implement `analyze()` method
3. Register in `app.py`
4. Update CLI if needed

### Adding New Merge Strategies

1. Add strategy to `ConflictResolver`
2. Update `rules.yaml` schema
3. Document in README

### Adding New Report Formats

1. Add format handler to `Reporter`
2. Implement `_generate_<format>_report()`
3. Update CLI choices

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock dependencies
- Focus on edge cases

### Integration Tests
- Test component interactions
- Use temporary directories
- Verify end-to-end workflows

### Test Coverage Goals
- Analyzers: 90%+
- Reconciler: 85%+
- Utilities: 90%+
- Overall: 85%+

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Only parse files when needed
2. **Caching**: Cache file hashes to avoid re-computation
3. **Parallel Processing**: Use multiprocessing for large directories (future)
4. **Streaming**: Stream large files instead of loading entirely

### Scalability

- Designed for 100s of files per version
- Can handle multiple versions (tested with 3-5)
- Memory-efficient file operations
- Configurable diff line limits

## Security Considerations

1. **Path Traversal**: Use `pathlib` for safe path operations
2. **Backup Safety**: Always backup before destructive operations
3. **Config Validation**: Validate user-provided configurations
4. **Sensitive Data**: Flag security-sensitive config keys

## Future Enhancements

1. **Git Integration**: Use git diff for version comparison
2. **Parallel Processing**: Speed up large directory scans
3. **Web UI**: Browser-based interface
4. **Rollback**: Undo merge operations
5. **Incremental Sync**: Sync changes between versions
6. **Plugin System**: Allow custom analyzers
