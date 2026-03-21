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

### 3. Action Builder (`nlcrud/api/action_builder.py`)
- **Purpose**: Convert intent + entities into structured CRUD action
- **Process**: Validates against database schema, maps entities to columns
- **Returns**: Action dict with operation type, resource, and parameters
- **Latency**: <1ms

### 4. Database Execution (`nlcrud/db/`)
- **Standard executor** (`executor.py`): Rule-based SQL generation
- **SQLCoder executor** (`sqlcoder_executor.py`): LLM-based SQL generation via Ollama
- **Configuration**: `USE_SQLCODER` environment variable
- **Features**: Fallback mechanisms, error handling, result formatting
- **Latency**: ~5ms (SQL execution)

### 5. API Layer (`nlcrud/api/app.py`)
- **Framework**: FastAPI
- **Main endpoint**: `POST /query` - Process natural language text
- **Debug endpoints**:
  - `GET /schema` - View database schema
  - `POST /compare_extractors` - Compare regex vs spaCy on same input
  - `POST /generate_sql` - Generate SQL without executing (SQLCoder only)
- **Logging**: Full pipeline execution printed to stdout for debugging

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
# Run all tests
python main.py test

# Run with all warnings visible
python main.py test --show-warnings

# Run specific test file
python test_nlcrud.py              # Main test suite
python test_sqlcoder.py            # SQLCoder tests
python test_ollama_direct.py       # Ollama connectivity tests
python test_data_flow.py           # Data flow tests
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
├── api/                              # REST API layer
│   ├── app.py                       # FastAPI application (main entry)
│   └── action_builder.py            # Intent + entities → action schema
├── intent_classification/            # Intent detection module
│   ├── classifier.py                # FastText wrapper
│   ├── model.py                     # Intent label definitions
│   ├── train.py                     # Model training
│   └── interface.py                 # Abstract interface
├── entity_extraction/                # Entity extraction module
│   ├── regex_extractor.py           # Fast regex-based
│   ├── spacy_extractor.py           # Accurate NER-based
│   └── interface.py                 # Abstract interface
├── db/                               # Database execution layer
│   ├── executor.py                  # Rule-based SQL generator
│   ├── sqlcoder_executor.py         # Ollama/LLM-based SQL generator
│   ├── schema.py                    # Database schema definitions
│   ├── init.py                      # Database initialization
│   └── interface.py                 # Abstract interface
├── utils/                            # Utility functions
├── cli.py                            # CLI argument parsing and server startup
└── tests/                            # Test utilities

db/
└── db.sqlite                        # SQLite database file

model/
└── intent.ftz                       # Trained FastText intent model

data/
└── intent_train.txt                 # Intent training data (FastText format)

Root level:
├── main.py                          # Unified CLI entry point
├── test_nlcrud.py                  # Main test suite
├── test_sqlcoder.py                # SQLCoder-specific tests
├── test_ollama_direct.py           # Ollama connectivity tests
├── test_data_flow.py               # Data flow integration tests
└── .env.example                     # Configuration template
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