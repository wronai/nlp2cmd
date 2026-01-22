# Installation Guide

## Quick Start

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/example/nlp2cmd.git
cd nlp2cmd

# Install with pip
pip install -e .
```

### Installation Options

#### 1. Minimal Installation (Rule-based DSL only)

```bash
pip install -e .
# or
pip install -r requirements-minimal.txt
```

**Features:**
- ✅ Rule-based intent detection
- ✅ Regex entity extraction  
- ✅ Template-based generation
- ❌ No LLM features
- ❌ No thermodynamic optimization

#### 2. Standard Installation (with LLM support)

```bash
pip install -e ".[llm]"
# or
pip install -r requirements.txt
```

**Additional Features:**
- ✅ All minimal features
- ✅ LLM integration (OpenAI, Anthropic)
- ✅ Structured JSON output
- ✅ Validation & self-correction
- ✅ Hybrid rule+LLM generation

#### 3. Full Installation (with Thermodynamic Optimization)

```bash
pip install -e ".[thermodynamic]"
# or
pip install -r requirements-thermodynamic.txt
```

**Additional Features:**
- ✅ All standard features
- ✅ Langevin dynamics sampling
- ✅ Energy-based optimization
- ✅ Scheduling & allocation solvers
- ✅ Energy efficiency monitoring

#### 4. Development Installation

```bash
pip install -e ".[dev]"
# or
pip install -r requirements.txt
```

**Additional Tools:**
- ✅ Testing framework
- ✅ Code formatting (black, ruff)
- ✅ Type checking (mypy)
- ✅ Documentation tools

## Dependencies

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `numpy` | `>=1.24.0` | Numerical computations, thermodynamic sampling |
| `pyyaml` | `>=6.0` | Configuration management |
| `pydantic` | `>=2.0` | Data validation |
| `rich` | `>=13.0` | Terminal output formatting |
| `click` | `>=8.0` | CLI interface |
| `httpx` | `>=0.25.0` | HTTP client for LLM APIs |
| `jinja2` | `>=3.0` | Template rendering |
| `jsonschema` | `>=4.0` | JSON schema validation |
| `python-dotenv` | `>=1.0` | Environment variables |
| `watchdog` | `>=3.0` | File system monitoring |

### Optional Dependencies

#### NLP Support
- `spacy>=3.7` - Advanced NLP processing

#### LLM Integrations
- `anthropic>=0.18` - Claude API
- `openai>=1.0` - OpenAI API

#### SQL Support
- `sqlparse>=0.4` - SQL parsing
- `sqlalchemy>=2.0` - SQL ORM

#### Thermodynamic Optimization
- `scipy>=1.10.0` - Scientific computing
- `matplotlib>=3.7.0` - Visualization

## System Requirements

- **Python**: 3.10 or higher
- **OS**: Linux, macOS, Windows
- **Memory**: 512MB minimum (thermodynamic features may require more)
- **Storage**: 100MB for installation

## Environment Setup

### Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv nlp2cmd-env

# Activate
# Linux/macOS:
source nlp2cmd-env/bin/activate
# Windows:
nlp2cmd-env\Scripts\activate

# Install
pip install -e ".[thermodynamic]"
```

### Docker Installation

```bash
# Build image
docker build -t nlp2cmd .

# Run container
docker run -it nlp2cmd
```

### Conda Installation

```bash
# Create conda environment
conda create -n nlp2cmd python=3.11
conda activate nlp2cmd

# Install
pip install -e ".[thermodynamic]"
```

## Configuration

### Environment Variables

```bash
# LLM API Keys (optional)
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Thermodynamic settings (optional)
export NLP2CMD_LANGEVIN_STEPS="500"
export NLP2CMD_ENERGY_THRESHOLD="0.7"
```

### Configuration File

Create `~/.nlp2cmd/config.yaml`:

```yaml
# LLM settings
llm:
  default_provider: "openai"
  temperature: 0.1
  max_tokens: 500

# Thermodynamic settings
thermodynamic:
  langevin_steps: 500
  temperature: 0.5
  mobility: 1.0
  n_samples: 5

# Hybrid settings
hybrid:
  confidence_threshold: 0.7
  enable_adaptive: true
```

## Verification

### Test Installation

```bash
# Test basic imports
python3 -c "from nlp2cmd.generation import create_hybrid_generator; print('✅ Basic OK')"

# Test thermodynamic features
python3 -c "from nlp2cmd.generation import create_thermodynamic_generator; print('✅ Thermodynamic OK')"

# Run demo
python3 termo_demo.py
```

### Run Tests

```bash
# Run all tests
pytest tests/iterative/ -v

# Run specific iteration tests
pytest tests/iterative/test_iter_10_thermodynamic.py -v
```

## Troubleshooting

### Common Issues

#### 1. ModuleNotFoundError: No module named 'numpy'
```bash
# Install numpy explicitly
pip install numpy>=1.24.0

# Or install with thermodynamic dependencies
pip install -e ".[thermodynamic]"
```

#### 2. LLM API Errors
```bash
# Check API keys
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Test without LLM
python3 -c "
from nlp2cmd.generation import create_hybrid_generator
gen = create_hybrid_generator()
print('✅ Rules-only mode works')
"
```

#### 3. Thermodynamic Performance Issues
```bash
# Reduce Langevin steps for faster execution
export NLP2CMD_LANGEVIN_STEPS="100"

# Or adjust in code
from nlp2cmd.thermodynamic import LangevinConfig
config = LangevinConfig(n_steps=100)
```

#### 4. Permission Errors
```bash
# Use user installation
pip install --user -e ".[thermodynamic]"

# Or use virtual environment
python3 -m venv nlp2cmd-env
source nlp2cmd-env/bin/activate
pip install -e ".[thermodynamic]"
```

### Performance Tips

1. **For simple DSL queries**: Use minimal installation for fastest startup
2. **For optimization problems**: Use thermodynamic installation with sufficient RAM
3. **For production**: Consider caching and batch processing
4. **For development**: Install dev dependencies for testing

## Uninstallation

```bash
# Uninstall package
pip uninstall nlp2cmd

# Remove virtual environment
deactivate
rm -rf nlp2cmd-env
```

## Next Steps

After installation:

1. **Quick Demo**: Run `python3 termo_demo.py`
2. **CLI Usage**: `nlp2cmd --help`
3. **Python API**: See `README_GENERATION.md`
4. **Thermodynamic Features**: See `THERMODYNAMIC_INTEGRATION.md`
5. **Development**: See `CONTRIBUTING.md`
