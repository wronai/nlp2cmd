# TODO - NLP2CMD Project

## 🚀 High Priority

### Enhanced NLP Integration
- [x] **Semantic Similarity**: sentence-transformers integration completed
- [x] **Multi-layer Pipeline**: Enhanced context detection with fallbacks
- [ ] **Performance Optimization**: Reduce memory usage for enhanced NLP
- [ ] **Custom Models**: Domain-specific fine-tuning for specialized vocabularies
- [ ] **Real-time Learning**: User feedback integration for model improvement

### Shell Emulation Enhancement
- [x] **Interactive Mode**: Full REPL with persistent session
- [x] **User Directory Recognition**: Smart "usera" → "~" mapping
- [ ] **Command History**: Persistent command history and favorites
- [ ] **Auto-completion**: Tab completion for commands and paths
- [ ] **Script Execution**: Batch processing of shell commands

### Browser DSL Development
- [x] **URL Navigation**: Basic URL detection and opening
- [x] **Search Integration**: Google, GitHub, Amazon search templates
- [ ] **Form Automation**: Advanced form filling with field mapping
- [ ] **Multi-tab Management**: Browser tab handling and switching
- [ ] **Screenshot Integration**: Visual feedback for browser actions

### Web Schema Engine
- [x] **Schema Extraction**: Basic element extraction completed
- [x] **Cache Integration**: Playwright browser caching implemented
- [ ] **Form Auto-filling**: Complete natural language to form field mapping
- [ ] **Multi-step Workflows**: Support for complex multi-page forms
- [ ] **CAPTCHA Handling**: Integration with CAPTCHA solving services

### Performance & Optimization
- [ ] **Parallel Processing**: Multi-threaded intent detection for batch queries
- [ ] **Memory Optimization**: Reduce memory footprint for large-scale processing
- [ ] **Cache Warming**: Pre-warm caches for common domains and patterns
- [ ] **Lazy Loading**: On-demand loading of NLP models and dependencies

## 🎯 Medium Priority

### CLI & User Experience
- [ ] **Interactive Mode Enhancement**: Rich interactive mode with auto-completion
- [ ] **Progress Indicators**: Better progress bars for long-running operations
- [ ] **Configuration Wizard**: Guided setup for new users
- [ ] **Plugin System**: Support for third-party plugins and extensions

### Integration & Ecosystem
- [ ] **API Server**: REST API for programmatic access
- [ ] **Web Interface**: Web-based UI for nlp2cmd functionality
- [ ] **IDE Extensions**: VS Code, JetBrains IDE extensions
- [ ] **CI/CD Integration**: GitHub Actions, GitLab CI templates

### Testing & Quality
- [ ] **E2E Test Suite**: Comprehensive end-to-end testing
- [ ] **Performance Benchmarks**: Automated performance regression testing
- [ ] **Security Audit**: Security assessment and hardening
- [ ] **Accessibility**: Screen reader and keyboard navigation support

## 🔧 Low Priority

### Advanced Features
- [ ] **Voice Input**: Speech-to-text integration for voice commands
- [ ] **Multi-language Support**: Beyond Polish (English, German, French)
- [ ] **Custom DSL Creation**: Tools for creating new domain-specific languages
- [ ] **Template Marketplace**: Community-driven template sharing

### Documentation & Examples
- [ ] **Video Tutorials**: Screen-cast tutorials for common workflows
- [ ] **Community Examples**: User-contributed examples and use cases
- [ ] **API Documentation**: Comprehensive API reference with examples
- [ ] **Troubleshooting Guide**: Advanced troubleshooting and debugging

### Infrastructure & DevOps
- [ ] **Docker Images**: Official Docker images for easy deployment
- [ ] **Kubernetes Charts**: Helm charts for production deployment
- [ ] **Monitoring Integration**: Prometheus/Grafana metrics
- [ ] **Log Aggregation**: ELK stack integration for centralized logging

## 🐛 Known Issues

### Polish NLP
- [ ] **Issue**: Some Polish diacritics not properly normalized in edge cases
- [ ] **Impact**: Medium - affects accuracy for some Polish inputs
- [ ] **Workaround**: Use fuzzy matching as fallback

### Web Schema
- [ ] **Issue**: Dynamic content (JavaScript-heavy sites) may not be fully captured
- [ ] **Impact**: Medium - affects some modern web applications
- [ ] **Workaround**: Use explicit waits and retry mechanisms

### Cache Management
- [ ] **Issue**: Cache size calculation may be inaccurate on some systems
- [ **Impact**: Low - cosmetic issue in cache reporting
- [ ] **Workaround**: Manual cache size verification

## 🔄 Backlog

### Research & Experimentation
- [ ] **LLM Integration**: Research GPT-4/Claude integration for complex queries
- [ ] **Graph-based Planning**: Knowledge graph for complex multi-step planning
- [ ] **Reinforcement Learning**: Self-improvement through user feedback
- [ ] **Federated Learning**: Privacy-preserving model improvements

### Legacy Support
- [ ] **Python 3.9 Support**: Extend support to Python 3.9
- [ ] **Windows Compatibility**: Full Windows support including PowerShell
- [ ] **ARM64 Support**: Apple Silicon and ARM64 optimization
- [ ] **Mobile Support**: iOS/Android app development

---

## 📊 Progress Tracking

### Completed in v1.0.20
- ✅ Web Schema Engine - Basic implementation
- ✅ Smart Cache Manager - External dependencies caching
- ✅ Polish NLP Enhancement - Lemmatization and fuzzy matching
- ✅ CLI Cache Commands - Full cache management suite

### In Progress
- 🔄 Form Auto-filling - Natural language to form mapping
- 🔄 Performance Optimization - Memory and speed improvements
- 🔄 Testing Suite - Comprehensive test coverage

### Next Release (v1.0.21)
- 🎯 Target: Enhanced web automation with form filling
- 🎯 Target: Performance improvements and memory optimization
- 🎯 Target: Expanded Polish language support

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

### How to Claim a Task
1. Open an issue describing the task you want to work on
2. Wait for maintainer approval
3. Create a feature branch from `main`
4. Implement the changes with tests
5. Submit a pull request with detailed description

### Task Priority Guidelines
- **High Priority**: Core functionality, security, performance
- **Medium Priority**: User experience, integrations, quality
- **Low Priority**: Nice-to-have features, documentation, infrastructure

---

## 📚 Documentation

### API Documentation
- [ ] **Concepts Module** - Complete API documentation for virtual objects
- [ ] **Environment Context** - Environment-aware API documentation
- [ ] **Dependency Resolution** - Dependency resolver API documentation
- [ ] **Semantic Objects** - Semantic object factory documentation

### User Guides
- [ ] **Advanced Usage** - Advanced features and customization guide
- [ ] **Troubleshooting** - Common issues and solutions guide
- [ ] **Best Practices** - Recommended usage patterns and tips
- [ ] **Migration Guide** - Migration from previous versions

### Developer Documentation
- [ ] **Architecture Guide** - System architecture and design decisions
- [ ] **Contributing Guide** - Contribution guidelines and standards
- [ ] **Plugin Development** - Plugin development guide
- [ ] **Performance Tuning** - Performance optimization guide

## 🎨 Features Wishlist

### AI/ML Enhancements
- [ ] **Custom Model Training** - Train domain-specific models
- [ ] **Few-Shot Learning** - Learn from few examples per user
- [ ] **Transfer Learning** - Leverage pre-trained models for new domains
- [ ] **Explainable AI** - Provide reasoning for command suggestions

### Domain Expansion
- [ ] **Database DSL** - SQL, NoSQL database command generation
- [ ] **Monitoring DSL** - System monitoring and alerting commands
- [ ] **Security DSL** - Security scanning and hardening commands
- [ ] **Analytics DSL** - Data analysis and visualization commands

### Integration Features
- [ ] **Shell Integration** - Native shell integration with aliases
- [ ] **Editor Plugins** - Editor plugins for seamless integration
- [ ] **Web Interface** - Web-based interface for command generation
- [ ] **Mobile App** - Mobile application for on-the-go usage

## 🔄 Maintenance Tasks

### Regular Maintenance
- [ ] **Dependency Updates** - Regular dependency security updates
- [ ] **Model Updates** - Update ML models with newer versions
- [ ] **Performance Monitoring** - Monitor and optimize performance metrics
- [ ] **User Feedback** - Collect and analyze user feedback

### Security
- [ ] **Security Audit** - Regular security audits and penetration testing
- [ ] **Dependency Scanning** - Automated vulnerability scanning
- [ ] **Input Validation** - Comprehensive input validation and sanitization
- [ ] **Access Control** - Role-based access control for enterprise features

---

## 📊 Progress Tracking

### Version 1.1.0 (Next Release)
- **Target**: Enhanced virtual objects and environment integration
- **Status**: 70% complete
- **ETA**: 2 weeks

### Version 1.2.0 (Future)
- **Target**: Advanced semantic understanding and performance optimization
- **Status**: Planning phase
- **ETA**: 1 month

### Version 2.0.0 (Long-term)
- **Target**: Full AI/ML integration with custom models
- **Status**: Research phase
- **ETA**: 3-6 months

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

### Quick Start for Contributors
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Areas Needing Help
- **Documentation**: Help improve documentation and user guides
- **Testing**: Expand test coverage and add integration tests
- **Performance**: Optimize performance and reduce memory usage
- **Internationalization**: Add support for more languages
- **Plugin Development**: Create plugins for new domains

### Task Priority Guidelines
- **High Priority**: Core functionality, security, performance
- **Medium Priority**: User experience, integrations, quality
- **Low Priority**: Nice-to-have features, documentation, infrastructure




użyj architektury  CQRS i event sourcing dla projektu, aby ułatwić procesowanie 

użyj schematycznego zapisu z głebią w postaci prostego do zrozumienia przez LLM z nawiasami jak w template i prostym DSL z toon, jak w project.functions.toon, aby jak najwiecej kontekstu opakowac w optymalnej formie w jednym pliku,
wszystko przenies do jendnego pliku toon co aktualnie jest w json i yamltylko podziel osobno schema i data oraz inne kategoria danych,
aby ładowanie i parsowanie i dostep do danych był wspoldzielony na kategoria a wpisy były dostepne dla wszystkich w jednym pliku

W celu uwtorzenia listy wszystkich mozliwych komend w systemie, 
jak generowac schema dokaldniej na podstawie testowania samej komendy, w celu zapoznnia jej calego api struktury
