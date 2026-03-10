"""
FastAPI application for Natural Language CRUD operations.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import os

# Import from our module structure
from nlcrud.intent_classification.classifier import classifier
from nlcrud.entity_extraction.regex_extractor import extract_entities as regex_extract_entities
from nlcrud.entity_extraction.spacy_extractor import extract_entities as spacy_extract_entities
from nlcrud.db.executor import execute
from nlcrud.db.schema import SCHEMA
from .action_builder import build_action

app = FastAPI(
    title="Natural Language CRUD API",
    description="Convert natural language commands into CRUD operations",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    text: str

class QueryResponse(BaseModel):
    action: dict
    result: dict
    latency_ms: float

@app.get("/")
def read_root():
    return {"message": "Welcome to Natural Language CRUD API"}

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """
    Process a natural language query and execute the corresponding CRUD operation.
    
    Args:
        request (QueryRequest): The request containing the natural language text
        
    Returns:
        QueryResponse: The action, result, and latency information
    """
    start_time = time.time()
    
    try:
        # Detect intent
        intent, confidence = classifier.predict(request.text)
        
        # Extract entities using spaCy by default
        # Use environment variable to control which extractor to use
        use_regex = os.environ.get("USE_REGEX_EXTRACTOR", "").lower() in ("true", "1", "yes")
        
        if use_regex:
            entities = regex_extract_entities(request.text)
        else:
            try:
                entities = spacy_extract_entities(request.text)
            except Exception as e:
                # Fallback to regex extractor if spaCy fails
                print(f"SpaCy extractor failed: {str(e)}. Falling back to regex extractor.")
                entities = regex_extract_entities(request.text)
        
        # Build action
        action = build_action(intent, entities)
        
        # Execute action
        result = execute(action)
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "action": action,
            "result": result,
            "latency_ms": latency_ms
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
def get_schema_info():
    """
    Get the available schema information.
    
    Returns:
        dict: The schema information
    """
    return {"schema": SCHEMA}

@app.post("/compare_extractors")
def compare_extractors_endpoint(request: QueryRequest):
    """
    Compare the results of both entity extractors for the same text.
    
    Args:
        request (QueryRequest): The request containing the natural language text
        
    Returns:
        dict: The results from both extractors
    """
    # Extract entities using both extractors
    regex_entities = regex_extract_entities(request.text)
    spacy_entities = spacy_extract_entities(request.text)
    
    return {
        "text": request.text,
        "regex_extractor": regex_entities,
        "spacy_extractor": spacy_entities
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("nlcrud.api.app:app", host="0.0.0.0", port=8000, reload=True)