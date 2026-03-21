"""FastAPI application for Natural Language CRUD operations."""
from fastapi import FastAPI, HTTPException

from nlcrud.api.handlers import QueryHandler, SQLGenerationHandler
from nlcrud.api.schemas import (
    QueryRequest,
    QueryResponse,
    GenerateSQLRequest,
    GenerateSQLResponse,
    CompareExtractorsRequest,
    CompareExtractorsResponse,
    SchemaResponse,
)
from nlcrud.exceptions import NLCRUDError
from nlcrud.entity_extraction.regex_extractor import extract_entities as regex_extract
from nlcrud.entity_extraction.spacy_extractor import extract_entities as spacy_extract
from nlcrud.db.schema import SCHEMA
from nlcrud.logger import get_logger

logger = get_logger("api")

app = FastAPI(
    title="Natural Language CRUD API",
    description="Convert natural language commands into CRUD operations",
    version="1.0.0"
)

# Initialize handlers
query_handler = QueryHandler()
sql_gen_handler = SQLGenerationHandler()

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to Natural Language CRUD API"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    """Process a natural language query and execute the corresponding CRUD operation.

    Args:
        request: The request containing the natural language text

    Returns:
        QueryResponse with action, result, and latency

    Raises:
        HTTPException: If processing fails
    """
    try:
        action, result, latency_ms = query_handler.handle(request.text)
        return QueryResponse(
            action=action.to_dict(),
            result=result,
            latency_ms=latency_ms
        )
    except NLCRUDError as e:
        logger.error(f"NLCRUD error in /query: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in /query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema", response_model=SchemaResponse)
def get_schema_info() -> SchemaResponse:
    """Get the available schema information.

    Returns:
        SchemaResponse with the database schema
    """
    logger.debug("Returning database schema")
    return SchemaResponse(schema=SCHEMA)

@app.post("/compare_extractors", response_model=CompareExtractorsResponse)
def compare_extractors_endpoint(request: QueryRequest) -> CompareExtractorsResponse:
    """Compare the results of both entity extractors for the same text.

    Args:
        request: The request containing the natural language text

    Returns:
        CompareExtractorsResponse with results from both extractors

    Raises:
        HTTPException: If extraction fails
    """
    try:
        logger.debug("Comparing entity extractors")
        regex_entities = regex_extract(request.text)
        spacy_entities = spacy_extract(request.text)

        return CompareExtractorsResponse(
            text=request.text,
            regex_extractor=regex_entities,
            spacy_extractor=spacy_entities
        )
    except Exception as e:
        logger.error(f"Error comparing extractors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_sql", response_model=GenerateSQLResponse)
def generate_sql_endpoint(request: QueryRequest) -> GenerateSQLResponse:
    """Generate SQL from natural language without executing it.

    This endpoint is only available when SQLCoder is enabled.

    Args:
        request: The request containing the natural language text

    Returns:
        GenerateSQLResponse with the generated SQL and action details

    Raises:
        HTTPException: If SQL generation fails or SQLCoder is not enabled
    """
    try:
        logger.debug("Generating SQL without execution")
        action, sql = sql_gen_handler.generate_sql(request.text)
        return GenerateSQLResponse(action=action.to_dict(), sql=sql)
    except NLCRUDError as e:
        logger.error(f"NLCRUD error in /generate_sql: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in /generate_sql: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("nlcrud.api.app:app", host="0.0.0.0", port=8000, reload=True)