# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**NLCRUD** is a Natural Language CRUD engine that converts natural language commands into structured CRUD operations and executes them against a SQLite database. It combines intent classification, entity extraction, and SQL execution in a modular pipeline.

**Key characteristics:**
- Low-latency query processing (~10-20ms total)
- Pluggable architecture for multiple implementations
- REST API interface via FastAPI
- LLM-based SQL generation via Ollama (optional)
- Two entity extraction methods: regex-based and spaCy NER

## Architecture Overview

The system processes user input through a linear pipeline:

```
User Input (natural language)
    ↓
Intent Classification (FastText)
    ↓
Entity Extraction (Regex or spaCy NER)
    ↓
Action Builder (intent + entities → structured action)
    ↓
Database Execution (Rule-based or LLM/Ollama-based)
    ↓
Response Formatter
```

## Core Modules

### 1. Intent Classification (`nlcrud/intent_classification/`)
- **Purpose**: Classify user input into CRUD operations (CREATE, READ, UPDATE, DELETE, SEARCH)
- **Implementation**: FastText ML model (`model/intent.ftz`)
- **Training data**: `data/intent_train.txt`
- **Key file**: `classifier.py`
- **Interface**: `classifier.predict(text) → (intent: str, confidence: float)`
- **Latency**: ~1ms

### 2. Entity Extraction (`nlcrud/entity_extraction/`)
- **Purpose**: Extract parameters from natural language (column names, values, IDs, etc.)
- **Two implementations**:
  - `regex_extractor.py`: Fast (~1ms), pattern-based, lower accuracy
  - `spacy_extractor.py`: Accurate, NER-based (~5-15ms), handles complex variations
- **Configuration**: `USE_REGEX_EXTRACTOR` environment variable
- **Interface**: `extract_entities(text: str) → Dict[str, Any]`

### 3. Action Builder (`nlcrud/action/`)
- **Purpose**: Convert intent + entities into structured CRUD action
- **Implementation**: `action/builder.py` - ActionBuilder class
- **Domain Model**: `action/action.py` - Action dataclass with validation
- **Process**: Validates against database schema, maps entities to columns
- **Returns**: Action object with operation type, resource, filters, and data
- **Latency**: <1ms
- **Files**:
  - `action/action.py` - Core Action domain object
  - `action/builder.py` - ActionBuilder implementation
  - `action/validator.py` - Action validation logic
  - `api/action_builder.py` - API layer re-exports

### 4. Database Execution (`nlcrud/db/`)
- **Standard executor** (`executor.py`): Rule-based SQL generation
- **SQLCoder executor** (`sqlcoder_executor.py`): LLM-based SQL generation via Ollama
- **Configuration**: `USE_SQLCODER` environment variable
- **Features**: Fallback mechanisms, error handling, result formatting
- **Latency**: ~5ms (SQL execution)

### 5. API Layer (`nlcrud/api/`)
- **Framework**: FastAPI
- **app.py**: Application setup and routes
  - `POST /query` - Process natural language text
  - `GET /schema` - View database schema
  - `POST /compare_extractors` - Compare regex vs spaCy on same input
  - `POST /generate_sql` - Generate SQL without executing (SQLCoder only)
- **handlers.py**: Business logic classes
  - `QueryHandler` - Process queries through full pipeline
  - `SQLGenerationHandler` - Generate SQL without execution
- **schemas.py**: Request/response validation
  - `QueryRequest`, `QueryResponse` - Main query interface
  - `ActionSchema` - Structured CRUD action
  - `GenerateSQLRequest/Response`, `SchemaResponse` - Other endpoints
- **action_builder.py**: Re-exports from `nlcrud.action` module

### 6. Infrastructure Modules

#### Configuration (`nlcrud/config.py`)
- Lazy-loaded configuration management
- `OllamaConfig` - LLM settings
- `DatabaseConfig` - Database settings
- `get_config()` - Get global configuration instance
- Environment variable overrides

#### Logging (`nlcrud/logger.py`)
- Structured logging setup using Python's logging module
- `get_logger(name)` - Get named logger instance
- `setup_logging(level)` - Initialize logging system
- All output goes through logger (not print statements)

#### Exception Hierarchy (`nlcrud/exceptions.py`)
- `NLCRUDError` - Base exception
- `IntentClassificationError` - Intent detection failures
- `EntityExtractionError` - Entity extraction failures
- `ActionBuildError` - Action building failures
- `ExecutionError` - Database execution failures
- `SQLGenerationError` - SQL generation failures
- Other domain-specific exceptions

## Common Development Commands

### Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Download spaCy language model (required for spaCy extractor)
python -m spacy download en_core_web_sm

# Initialize database with schema
python -m nlcrud.db.init

# Train intent classification model
python -m nlcrud.intent_classification.train
```

### Running the Server
```bash
# Standard mode (rule-based SQL)
python main.py serve --reload

# With spaCy extractor (default, more accurate)
python main.py serve --extractor spacy --reload

# With regex extractor (faster)
python main.py serve --extractor regex --reload

# With debug logging
python main.py serve --log-level debug

# With all warnings visible
python main.py serve --show-warnings
```

### Running with Ollama/SQLCoder
```bash
# Enable SQLCoder with Ollama
USE_SQLCODER=true python main.py serve --reload

# Or set in .env file, then run normally
python main.py serve --reload
```

### Running Tests
```bash
# Run all tests with pytest
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=nlcrud

# Run specific test file
pytest tests/unit/test_pipeline.py              # Unit tests
pytest tests/integration/test_query_pipeline.py # Integration tests
pytest tests/integration/test_sqlcoder_executor.py  # SQLCoder tests
```

### Direct Server Invocation (alternative)
```bash
# Using uvicorn directly
uvicorn nlcrud.api.app:app --reload
```

## Package Management

**Use `uv` for all package management:**
```bash
# Install dependencies
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run Python commands
uv run python main.py serve

# Don't use: pip, pip3, poetry, or setuptools directly
```

See `pyproject.toml` for dependency definitions.

## Configuration

### Environment Variables

**Extractor selection:**
```
USE_REGEX_EXTRACTOR=true   # Use regex extractor (default: false, uses spaCy)
```

**SQLCoder/Ollama configuration:**
```
USE_SQLCODER=true                           # Enable LLM-based SQL generation
OLLAMA_URL=http://localhost:11434/api/generate  # Ollama endpoint
OLLAMA_MODEL=sqlcoder                      # Model name
```

**Create `.env` file in project root:**
```
USE_SQLCODER=true
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=sqlcoder
```

### Ollama Setup

1. **Install Ollama** from [ollama.ai](https://ollama.ai)
2. **Pull SQLCoder model**:
   ```bash
   ollama pull sqlcoder
   ```
3. **Start Ollama** (runs as background service on most systems)
4. **Set environment variables** and start the server:
   ```bash
   USE_SQLCODER=true python main.py serve --reload
   ```

## Project Structure

```
nlcrud/
├── action/                           # CRUD action domain and building
│   ├── action.py                    # Action dataclass with validation
│   ├── builder.py                   # ActionBuilder class (intent+entities → action)
│   ├── validator.py                 # Action validation logic
│   └── __init__.py                  # Module exports
├── api/                              # REST API layer
│   ├── app.py                       # FastAPI application setup and routes
│   ├── handlers.py                  # QueryHandler and SQLGenerationHandler
│   ├── schemas.py                   # Pydantic request/response models
│   └── action_builder.py            # Re-exports from nlcrud.action
├── intent_classification/            # Intent detection module
│   ├── classifier.py                # FastText wrapper and classifier
│   ├── model.py                     # Intent label definitions
│   ├── train.py                     # Model training script
│   ├── interface.py                 # Abstract EntityExtractor interface
│   └── __init__.py
├── entity_extraction/                # Entity extraction module
│   ├── regex_extractor.py           # Fast regex-based extraction
│   ├── spacy_extractor.py           # Accurate NER-based extraction
│   ├── interface.py                 # Abstract interface
│   └── __init__.py
├── db/                               # Database execution layer
│   ├── executor.py                  # RuleBasedExecutor: deterministic SQL generation
│   ├── sqlcoder_executor.py         # SQLCoderExecutor: LLM-based SQL via Ollama
│   ├── interface.py                 # DatabaseExecutor abstract interface
│   ├── schema.py                    # Database schema definitions
│   ├── init.py                      # Database initialization and seeding
│   ├── models/                      # Domain models for type-safety
│   │   ├── user.py                  # User entity model
│   │   ├── order.py                 # Order entity model
│   │   └── __init__.py
│   └── __init__.py
├── config.py                         # Centralized configuration management
├── logger.py                         # Logging infrastructure setup
├── exceptions.py                     # Custom exception hierarchy
├── cli.py                            # CLI entry point and argument parsing
└── __init__.py

db/
└── db.sqlite                        # SQLite database file

model/
└── intent.ftz                       # Trained FastText intent model

data/
└── intent_train.txt                 # Intent training data (FastText format)

tests/                               # Test suite
├── unit/                            # Unit tests
│   └── test_pipeline.py            # Pipeline component tests
├── integration/                     # Integration tests
│   ├── test_query_pipeline.py      # End-to-end query processing
│   ├── test_query_pipeline.py      # SpaCy extractor integration
│   ├── test_sqlcoder_executor.py   # SQLCoder executor tests
│   └── test_ollama_connectivity.py # Ollama API connectivity
├── conftest.py                      # Pytest configuration and fixtures
└── fixtures/                        # Shared test fixtures

Root level:
├── main.py                          # Unified CLI entry point
├── pyproject.toml                   # Modern Python project configuration
├── requirements.txt                 # Dependency list (for reference)
├── setup.py                         # Legacy setuptools config (deprecated)
├── Makefile                         # Development task automation
├── pytest.ini                       # Pytest configuration
├── .pre-commit-config.yaml          # Pre-commit hooks configuration
├── .env.example                     # Configuration template
└── scripts/                         # Utility scripts
    └── enforce_uv.sh               # UV package manager enforcement
```

## Architecture Design Patterns

### Dynamic Implementation Selection
The app chooses implementations at runtime based on environment variables:
- `executor.py` vs `sqlcoder_executor.py` based on `USE_SQLCODER`
- `regex_extractor.py` vs `spacy_extractor.py` based on `USE_REGEX_EXTRACTOR`

This enables testing different implementations without code changes.

### Fallback Mechanisms
- **Entity Extraction**: Falls back from spaCy to regex if NER fails
- **SQLCoder**: Falls back to rule-based SQL generation if LLM fails
- **SQL Extraction**: Handles messy LLM responses by extracting clean SQL from various formats

### Module Extensibility
To add a new implementation:
1. Create new file in appropriate module (e.g., `entity_extraction/my_extractor.py`)
2. Implement the same interface as existing implementations
3. Add environment variable switch in `app.py` or `cli.py`

## Debugging & Development

### Verbose Pipeline Output
The `/query` endpoint prints the entire execution pipeline to stdout:

```
===== INTENT CLASSIFICATION LAYER =====
Input text: '...'
Detected intent: ..., confidence: ...

===== ENTITY EXTRACTION LAYER =====
Using extractor: spacy
Extracted entities: {...}

===== ACTION BUILDER LAYER =====
Built action: {...}

===== DATABASE EXECUTION LAYER =====
Execution result: {...}
```

Use `--log-level debug` for additional logging.

### Diagnostic Endpoints
- `POST /query` — Main query processing (see verbose output above)
- `GET /schema` — View current database schema
- `POST /compare_extractors` — Run both extractors, compare results
- `POST /generate_sql` — Generate SQL without executing (SQLCoder only)

### Common Issues

| Issue | Solution |
|-------|----------|
| spaCy model not found | `python -m spacy download en_core_web_sm` |
| FastText model not found | `python -m nlcrud.intent_classification.train` |
| Database doesn't exist | `python -m nlcrud.db.init` |
| Ollama not responding | Verify Ollama is running: `curl http://localhost:11434/api/generate` |
| NumPy warnings | Normal, suppressed by default; use `--show-warnings` to see |
| SQLCoder returns invalid SQL | Check Ollama model; fallback to rule-based executor |

## Testing Strategy

- **Unit tests** (`test_nlcrud.py`): Test individual components (intent, entity extraction)
- **Integration tests** (`test_sqlcoder.py`): Test end-to-end with Ollama
- **Connectivity tests** (`test_ollama_direct.py`): Test Ollama availability
- **Data flow tests** (`test_data_flow.py`): Test complete pipeline
- Run all: `python main.py test`
- Run one: `python test_nlcrud.py`

## Performance

| Component | Latency | Notes |
|-----------|---------|-------|
| Intent classification | ~1ms | FastText model |
| Entity extraction (regex) | ~1ms | Fast, lower accuracy |
| Entity extraction (spaCy) | ~5-15ms | Accurate NER |
| SQL execution | ~5ms | SQLite query time |
| **Total (regex)** | **~10ms** | |
| **Total (spaCy)** | **~15-20ms** | Recommended; better accuracy |

spaCy extractor trades ~5-10ms latency for significantly better accuracy on complex queries.

## SQLCoder Implementation Details

### How It Works
1. **Prompt construction**: Builds prompt with schema, query, and guidelines
2. **LLM call**: Sends to Ollama for SQL generation
3. **SQL extraction**: Parses LLM response (handles code blocks, quotes, etc.)
4. **Execution**: Runs extracted SQL against SQLite
5. **Fallback**: If extraction fails, falls back to rule-based SQL generation

### Key Features
- **Robust extraction**: Handles messy LLM responses with multiple parsing strategies
- **Multi-level fallback**: LLM → rule-based SQL → original executor
- **Error resilience**: Logs errors but continues functioning
- **Same interface**: Swappable with rule-based executor

### Testing SQLCoder
```bash
# Test with Ollama running
USE_SQLCODER=true python test_sqlcoder.py

# Test Ollama connectivity directly
python test_ollama_direct.py

# Try a query via API
curl -X POST "http://localhost:8000/generate_sql" \
  -H "Content-Type: application/json" \
  -d '{"text": "find users older than 30"}'
```

## Notes

- **Warnings suppressed by default**: Keep output clean; use `--show-warnings` during debugging
- **Environment variables preferred**: No config files; all settings via `.env` or shell
- **.env is gitignored**: Use `.env.example` as template
- **SQLCoder is a POC**: Currently Ollama-only; hardcoded fallback to rule-based SQL
- **CLI filters**: `cli.py` suppresses numpy/cryptography warnings unrelated to functionality
- **Git status**: Working files modified; `.env` and test files are work-in-progress