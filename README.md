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
Entity Extraction (Regex + Schema Dictionary)
   ↓
Action Builder (Structured CRUD Schema)
   ↓
Execution Layer (SQL Generator)
   ↓
Response Formatter
```

## Project Structure

```
nlcrud/
│
├── app.py                 # FastAPI application
├── intent_classifier.py   # Production-ready intent classifier
├── entity_extractor.py    # Entity extraction logic
├── action_builder.py      # Action building logic
├── executor.py            # SQL execution engine
├── schema.py              # Schema definition
├── train_intent.py        # Intent model training script
├── test_nlcrud.py         # Test script
├── init_db.py             # Database initialization script
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

3. Initialize the database:
```
python init_db.py
```

4. Train the intent model:
```
python train_intent.py
```

## Usage

### Running the API Server

```
uvicorn app:app --reload
```

The API will be available at http://localhost:8000

### API Endpoints

- `GET /`: Welcome message
- `POST /query`: Process a natural language query
- `GET /schema`: Get the available schema information

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
```

## Performance

| Component | Latency |
|-----------|--------|
| Intent classification | ~1 ms |
| Entity extraction | ~1 ms |
| SQL execution | ~5 ms |

Total expected latency: ~10ms

## Model Footprint

| Component | Size |
|-----------|------|
| FastText model | ~5MB |
| Application code | ~1MB |

Total system size: <10MB

## Future Improvements

- Add NER model for better entity extraction
- Add embedding model for semantic schema matching
- Add REST API adapter for external systems
- Add workflow execution engine
- Add permission system
- Add multi-resource joins
- Add query planning

## License

MIT