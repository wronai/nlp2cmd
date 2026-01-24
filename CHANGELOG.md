# Changelog

All notable changes to NLP2CMD will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.21] - 2026-01-24

### 🚀 Major Features
- **Enhanced NLP Integration** - Advanced semantic similarity and context detection
- **Shell Emulation Mode** - Full interactive shell with natural language commands
- **Browser DSL Support** - New browser domain with URL navigation and search
- **Multi-layer Intent Detection** - Enhanced pipeline with fallback mechanisms

### 🧠 Enhanced NLP Improvements
- **Semantic Similarity**: sentence-transformers integration for conceptual understanding
- **Context Awareness**: Web schema integration for browser automation context
- **Polish Language Enhancement**: Improved diacritics and typo handling
- **Confidence Scoring**: Multi-layered confidence calculation with metrics
- **Fallback Pipeline**: Graceful degradation from enhanced to basic detection

### 🖥️ Shell Emulation
- **Interactive Mode**: `nlp2cmd --interactive --dsl shell` with persistent session
- **User Directory Recognition**: Smart handling of "usera" → "~" mapping
- **Process Management**: Enhanced process and service command detection
- **Real-time Feedback**: YAML output with detailed metrics and suggestions
- **Polish Commands**: Native Polish shell command support

### 🌐 Browser Automation
- **URL Navigation**: Automatic URL detection and opening
- **Search Integration**: Google, GitHub, Amazon search templates
- **Form Interaction**: Element clicking and form filling patterns
- **Web Context**: Integration with web schema extraction results

### 🔧 Pipeline Enhancements
- **RuleBasedPipeline**: Enhanced pipeline with context detection
- **Enhanced Context**: Optional enhanced NLP with graceful fallback
- **Markdown Stripping**: Automatic cleanup of LLM code block responses
- **Entity Extraction**: Improved regex patterns for browser and shell entities
- **Template Generation**: New browser templates for web actions

### 📊 Performance & Metrics
- **Resource Monitoring**: Detailed CPU, memory, and energy metrics
- **Token Estimation**: LLM token usage and cost calculation
- **Processing Time**: Per-layer timing analysis
- **Confidence Tracking**: Which detection method succeeded

### 🛠️ CLI Improvements
- **Interactive Shell**: Enhanced REPL with environment detection
- **Help System**: Improved command documentation and examples
- **Error Handling**: Better error messages and recovery
- **Output Formatting**: Rich YAML output with structured data

### 📚 Documentation
- **Enhanced NLP Guide**: Comprehensive enhanced NLP integration documentation
- **Shell Emulation Examples**: Real-world interactive shell examples
- **Browser Automation**: Web automation patterns and templates
- **Performance Metrics**: Resource monitoring and optimization guide

### 🧪 Testing & Quality
- **Enhanced Test Coverage**: Tests for new NLP features
- **Interactive Mode Testing**: Shell emulation validation
- **Browser Pattern Tests**: URL and search pattern verification
- **Performance Benchmarks**: Resource usage monitoring

## [1.0.20] - 2026-01-24

### 🚀 Major Features

- **Web Schema Engine** - Complete browser automation system with Playwright integration
- **Smart Cache Manager** - External dependencies caching for Playwright browsers (3105+ MB saved)
- **Polish NLP Enhancement** - Advanced lemmatization, fuzzy matching, and diacritics normalization
- **CLI Cache Commands** - Full cache management suite (`nlp2cmd cache`)

### 🌐 Web Automation

- **Schema Extraction**: `nlp2cmd web-schema extract <url>` - Extract interactive elements from any website
- **Form Filling**: Automatic form detection and filling with natural language
- **Interaction History**: Track and analyze web interactions with success rates
- **Learned Schemas**: Export learned patterns from interaction history
- **Multi-browser Support**: Chromium, Firefox, WebKit with automatic fallback

### 🧠 NLP Improvements

- **Polish Lemmatization**: spaCy integration for advanced Polish language processing
- **Fuzzy Matching**: rapidfuzz integration for typo tolerance (95%+ accuracy)
- **Diacritics Normalization**: ł→l, ę→e, ą→a for robust Polish text handling
- **Multi-word Keywords**: Flexible spacing pattern matching for complex phrases
- **Confidence Scoring**: Enhanced intent detection with confidence metrics
- **Priority Detection**: Service-related intents prioritized over generic patterns

### 💾 Cache Management

- **External Cache**: `~/.cache/external/` for Playwright browsers and dependencies
- **Auto-Setup**: `nlp2cmd cache auto-setup` - One-click installation and configuration
- **Smart Detection**: Automatic cache usage with fallback to fresh installation
- **Size Optimization**: 3105.4 MB browsers cached and shared across commands
- **Manifest Tracking**: JSON manifest with metadata and installation history

### 🛠️ CLI Enhancements

- **Cache Commands**: `setup|install|info|check|clear|auto-setup`
- **Web Schema Commands**: `extract|history|export-learned|clear`
- **Enhanced Help**: Rich formatting with progress bars and status indicators
- **Error Recovery**: Better error messages and automatic dependency resolution

### 🧪 Testing & Quality

- **Test Suite**: 8/9 tests passing with comprehensive coverage
- **Polish Language Tests**: Specific test cases for Polish diacritics and typos
- **Web Schema Tests**: End-to-end browser automation validation
- **Cache Tests**: External dependency caching verification

### 📚 Documentation Updates

- **README Update**: Complete rewrite with Quick Start guide and feature highlights
- **Web Schema Guide**: New documentation for browser automation
- **Cache Management Guide**: External dependencies caching documentation
- **Examples**: Real-world usage examples with Polish language support

### 🔧 Internal Improvements

- **Pattern Matching**: Regex-based multi-word keyword detection
- **Performance**: Optimized keyword detection with reduced false positives
- **Modularity**: Separated cache management into dedicated utilities
- **Error Handling**: Enhanced exception handling and user feedback

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
