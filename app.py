from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import time
import uvicorn

from intent_classifier import classifier
# Import both entity extractors
from entity_extractor import extract_entities as regex_extract_entities
from spacy_entity_extractor import extract_entities as spacy_extract_entities
from action_builder import build_action
from executor import execute
import os

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
def get_schema():
    """
    Get the available schema information.
    
    Returns:
        dict: The schema information
    """
    from schema import SCHEMA
    return {"schema": SCHEMA}

@app.post("/compare_extractors")
def compare_extractors(request: QueryRequest):
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
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)