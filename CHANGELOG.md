# Changelog

All notable changes to NLP2CMD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-01-23

### Added
- Comprehensive documentation cross-linking between all markdown files
- Navigation sections in all documentation files with related links
- Examples section in README.md with categorized links to practical examples
- Documentation links in example Python files (basic_sql.py, basic_shell.py, end_to_end_demo.py)
- Central documentation hub at docs/README.md with complete navigation structure
- Links to scientific papers and references for thermodynamic optimization
- Quick navigation by use case (new users, developers, domain-specific applications)

### Improved
- Enhanced documentation discoverability and user experience
- Better integration between API docs, user guides, and examples
- Clearer documentation structure with hierarchical navigation

## [Unreleased]

### Added
- Initial release of NLP2CMD framework
- SQL adapter with PostgreSQL, MySQL, SQLite, MSSQL support
- Shell adapter with Bash, Zsh, Fish, PowerShell support
- Docker adapter with CLI and Compose support
- Kubernetes adapter with kubectl command generation
- DQL (Doctrine Query Language) adapter for PHP/Symfony
- Schema Registry for file format validation and repair
- Supported formats: Dockerfile, docker-compose, Kubernetes manifests, GitHub Actions, .env files
- Feedback loop with automatic error correction suggestions
- Environment analyzer for tool and service detection
- Interactive REPL mode with intelligent feedback
- Safety policies for all DSL types
- LLM integration support (Claude, GPT)
- CLI tool with comprehensive options
- Full test coverage
- API documentation
- User guide

### Security
- Comprehensive safety policies for each DSL type
- Blocked dangerous commands and patterns
- Confirmation requirements for destructive operations
- Namespace and table restrictions

## [0.1.0] - 2024-XX-XX

### Added
- Initial public release

---

## Types of Changes

- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` for vulnerability fixes
