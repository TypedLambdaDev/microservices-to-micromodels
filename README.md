# Natural Language CRUD Engine

A lightweight Natural Language CRUD engine that converts natural language commands into structured CRUD actions and executes them against a SQL database.

## Features

- Converts natural language commands into CRUD actions
- Supports CREATE, READ, UPDATE, DELETE, SEARCH operations
- Works with SQL databases (SQLite initially)
- Uses a small ML model (FastText)
- Low latency (<10ms)
- Runs locally
- Provides a REST API interface

## System Architecture

```
User Input
   ↓
Intent Detection (FastText)
   ↓
Entity Extraction (spaCy NER + Regex Fallback)
   ↓
Action Builder (Structured CRUD Schema)
   ↓
Execution Layer (SQL Generator)
   ↓
Response Formatter
```

## Project Structure

```
/
│
├── main.py                # Main entry point for all functionality
├── test_nlcrud.py         # Test script for natural language queries
│
├── nlcrud/                # Main package
│   ├── api/               # API-related code
│   │   ├── app.py         # FastAPI application
│   │   └── action_builder.py # Action building logic
│   │
│   ├── entity_extraction/ # Entity extraction modules
│   │   ├── regex_extractor.py # Regex-based entity extractor
│   │   ├── spacy_extractor.py # spaCy-based entity extractor
│   │   └── interface.py   # Unified interface for entity extraction
│   │
│   ├── intent_classification/ # Intent classification modules
│   │   ├── classifier.py  # Intent classifier implementation
│   │   ├── model.py       # Intent model definition
│   │   ├── train.py       # Training script
│   │   └── interface.py   # Unified interface for intent classification
│   │
│   ├── db/                # Database-related code
│   │   ├── executor.py    # SQL execution engine
│   │   ├── schema.py      # Schema definition
│   │   ├── init.py        # Database initialization
│   │   └── interface.py   # Unified interface for database operations
│   │
│   └── utils/             # Utility functions
│
├── model/
│   └── intent.ftz         # Trained FastText model
│
├── data/
│   └── intent_train.txt   # Training data for intent model
│
└── db/
    └── db.sqlite          # SQLite database
```

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/nlcrud.git
cd nlcrud
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Download the spaCy language model:
```
python -m spacy download en_core_web_sm
```

3. Initialize the database:
```
python -m nlcrud.db.init
```

4. Train the intent model:
```
python -m nlcrud.intent_classification.train
```

## Usage

The application provides a unified command-line interface for all functionality:

### Starting the Server

```
python main.py serve [options]
```

Options:
- `--host HOST`: Host to bind to (default: 0.0.0.0)
- `--port PORT`: Port to bind to (default: 8000)
- `--reload`: Enable auto-reload for development
- `--extractor {regex,spacy}`: Entity extractor to use (default: spacy)
- `--show-warnings`: Show all warnings (by default, warnings are suppressed)
- `--log-level {debug,info,warning,error,critical}`: Set the logging level (default: info)

Example:
```
python main.py serve --port 8080 --reload --extractor regex
```

### Running Tests

```
python main.py test [options]
```

Options:
- `--show-warnings`: Show all warnings (by default, warnings are suppressed)

Example:
```
python main.py test
```

### Running the API Server

```
# Using the main.py entry point
python main.py

# Using the CLI after installation
nlcrud serve --reload

# Or directly with uvicorn
uvicorn nlcrud.api.app:app --reload
```

### CLI Options

The NLCRUD CLI provides several options for running the server:

```
nlcrud serve --host 0.0.0.0 --port 8000 --reload --extractor spacy
```

Options:
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 8000)
- `--reload`: Enable auto-reload for development
- `--extractor`: Entity extractor to use (choices: regex, spacy; default: spacy)

### Using with uv

This project is compatible with [uv](https://github.com/astral-sh/uv), the fast Python package installer and resolver:

```
# Install uv
curl -sSf https://astral.sh/uv/install.sh | bash

# Install the project with uv
uv pip install -e .

# Install with development dependencies
uv pip install -e ".[dev]"
```

The API will be available at http://localhost:8000

### API Endpoints

- `GET /`: Welcome message
- `POST /query`: Process a natural language query
- `GET /schema`: Get the available schema information
- `POST /compare_extractors`: Compare results from both entity extractors

### Example Queries

```bash
# Show all users
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"text": "show all users"}'

# Get a specific user
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"text": "get user with id 1"}'

# Create a new user
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"text": "create user with name John and email john@example.com and age 30"}'

# Update a user
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"text": "update user with id 1 set email to updated@example.com"}'

# Delete a user
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"text": "delete user with id 3"}'

# Search for users
curl -X POST "http://localhost:8000/query" -H "Content-Type: application/json" -d '{"text": "find users with age 30"}'

# Compare both entity extractors
curl -X POST "http://localhost:8000/compare_extractors" -H "Content-Type: application/json" -d '{"text": "find users who are 30 years old with email john@example.com"}'
```

## Performance

| Component | Latency (Regex) | Latency (spaCy) |
|-----------|----------------|-----------------|
| Intent classification | ~1 ms | ~1 ms |
| Entity extraction | ~1 ms | ~5-10 ms |
| SQL execution | ~5 ms | ~5 ms |

Total expected latency:
- With regex extractor: ~10ms
- With spaCy extractor: ~15-20ms

The spaCy-based entity extractor provides better accuracy at the cost of slightly higher latency. For most applications, the improved accuracy outweighs the small increase in processing time.

### Detailed Latency Comparison

Based on our testing, here are the detailed latency measurements:

| Query Type | Regex Extractor | spaCy Extractor |
|------------|----------------|-----------------|
| Simple queries (e.g., "show all users") | 1-2 ms | 5-7 ms |
| Medium complexity (e.g., "get user with id 5") | 2-3 ms | 7-10 ms |
| Complex queries (e.g., "find users who are 30 years old with email john@example.com") | 3-5 ms | 10-15 ms |

While the spaCy extractor is consistently 5-10ms slower than the regex approach, it provides significantly better entity extraction accuracy, especially for complex natural language queries. The trade-off is minimal for most applications where response times under 50ms are still considered real-time.

## Model Footprint

| Component | Size |
|-----------|------|
| FastText model | ~5MB |
| Application code | ~1MB |
| spaCy model (en_core_web_sm) | ~13MB |

Total system size:
- Without spaCy: <10MB
- With spaCy: ~25MB

## Entity Extraction

The system supports two different entity extraction methods:

### 1. Regex-based Entity Extraction (Original)

The original implementation uses regular expressions to extract entities from text. This approach is:
- Lightweight and fast
- Requires no additional dependencies
- Works well for simple patterns
- May struggle with complex language variations

### 2. spaCy-based Entity Extraction (New)

The new implementation uses spaCy's Named Entity Recognition (NER) capabilities:
- More accurate for complex natural language
- Better handling of context and variations
- Custom entity recognition for domain-specific entities
- Fallback to regex for certain patterns

You can switch between extractors in several ways:

#### Using environment variables:
```
# Use regex extractor
export USE_REGEX_EXTRACTOR=true
python main.py

# Use spaCy extractor (default)
python main.py
```

#### Using the CLI:
```
# Use regex extractor
nlcrud serve --extractor regex

# Use spaCy extractor
nlcrud serve --extractor spacy
```

#### Using direct uvicorn command:
```
# Use regex extractor
export USE_REGEX_EXTRACTOR=true
uvicorn nlcrud.api.app:app --reload

# Use spaCy extractor
uvicorn nlcrud.api.app:app --reload
```

You can also compare both extractors using the `/compare_extractors` endpoint.

## Modular Package Structure

The codebase has been reorganized into a modular package structure with the following benefits:

- **Separation of Concerns**: Each module has a clear responsibility
- **Better Maintainability**: Easier to understand and modify individual components
- **Improved Testability**: Components can be tested in isolation
- **Cleaner Interfaces**: Each module exposes a well-defined interface
- **Extensibility**: New implementations can be added without modifying existing code

The new structure follows these design principles:

1. **Interface Segregation**: Each module provides a clean interface that hides implementation details
2. **Dependency Inversion**: High-level modules depend on abstractions, not concrete implementations
3. **Single Responsibility**: Each module has one clear purpose
4. **Open/Closed**: The system is open for extension but closed for modification

## Future Improvements

- ✅ Add NER model for better entity extraction
- Add embedding model for semantic schema matching
- Add REST API adapter for external systems
- Add workflow execution engine
- Add permission system
- Add multi-resource joins
- Add query planning

## License

MIT