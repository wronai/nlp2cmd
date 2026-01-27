# NLP2CMD Project Structure

This document describes the reorganized project structure for better maintainability and clarity.

## Directory Structure

```
nlp2cmd/
├── src/                     # Source code
│   └── nlp2cmd/            # Main package
├── examples/               # Example scripts and demos
│   ├── architecture/       # Architecture examples
│   ├── benchmark_*.py      # Performance benchmarking tools
│   ├── devops/            # DevOps examples
│   ├── docker/            # Docker examples
│   ├── shell/             # Shell command examples
│   ├── sql/               # SQL examples
│   └── use_cases/         # Real-world use cases
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/               # End-to-end tests
│   └── iterative/         # Iterative test scenarios
├── scripts/                # Utility scripts
│   ├── maintenance/        # Maintenance and setup scripts
│   ├── testing/           # Testing utilities
│   ├── thermodynamic/     # Thermodynamic optimization scripts
│   ├── test-scripts/      # Individual test scripts
│   └── bump_version.py    # Version management
├── docs/                   # Documentation
├── data/                   # Data files and configurations
├── command_schemas/        # Command schema definitions
├── artifacts/              # Build and test artifacts
└── tools/                  # Development tools
```

## Script Categories

### Maintenance Scripts (`scripts/maintenance/`)
Scripts for project maintenance, setup, and fixes:
- `apply_*.py` - Apply various fixes and integrations
- `fix_*.py` - Fix specific issues
- `implement_*.py` - Implement features
- `final_*.py` - Analysis and summary scripts
- `restore_system.py` - System restoration

### Thermodynamic Scripts (`scripts/thermodynamic/`)
Scripts related to thermodynamic optimization:
- `termo.py` - Core thermodynamic implementation
- `termo1.py` - Simplified version
- `termo2.py` - Advanced implementation
- `termo_demo.py` - Demonstration script

### Testing Scripts (`scripts/testing/`)
Utilities for testing:
- `run_e2e_tests.py` - End-to-end test runner

### Examples (`examples/`)
- `benchmark_nlp2cmd.py` - Performance benchmarking tool
- `benchmark_sequential_commands.py` - Sequential command benchmark
- Domain-specific examples in subdirectories

## Makefile Integration

The Makefile has been updated to reflect the new structure:

### Benchmarking
```bash
make report              # Generate benchmark report
make demo-benchmark      # Run benchmark demo
make benchmark-view      # View last benchmark
make benchmark-md        # View markdown report
```

### Script Management
```bash
make scripts-maintenance # List maintenance scripts
make scripts-thermo      # List thermodynamic scripts
make scripts-test        # List testing scripts
make scripts-all         # List all scripts
make run-thermo          # Run thermodynamic demo
```

### Development
```bash
make demo                # Run main demo
make bump-patch          # Bump patch version
```

## File Relocations

The following files have been moved:
- `benchmark_nlp2cmd.py` → `examples/benchmark_nlp2cmd.py`
- `test_form_detection.py` → `tests/test_form_detection.py`
- `run_e2e_tests.py` → `scripts/testing/run_e2e_tests.py`
- `termo*.py` → `scripts/thermodynamic/`
- `apply_*.py`, `fix_*.py`, `implement_*.py`, `final_*.py` → `scripts/maintenance/`
- `bump_version.py` → `scripts/bump_version.py`

## Benefits of New Structure

1. **Better Organization**: Scripts are categorized by purpose
2. **Easier Maintenance**: Related files are grouped together
3. **Clearer Examples**: All examples in one directory
4. **Improved Discoverability**: Makefile targets for each category
5. **Scalability**: Easy to add new scripts to appropriate categories

## Adding New Scripts

When adding new scripts:
1. Choose appropriate category:
   - `examples/` for demonstration scripts
   - `scripts/maintenance/` for setup/maintenance utilities
   - `scripts/testing/` for testing utilities
   - `scripts/thermodynamic/` for thermodynamic-related code
2. Update Makefile if needed
3. Add documentation in appropriate doc file

## Migration Notes

- All imports have been updated to reflect new locations
- Makefile targets updated
- Documentation refreshed
- No functional changes - only file organization
