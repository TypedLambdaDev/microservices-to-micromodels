"""Pydantic schemas for API requests and responses.

Defines the contract between client and API.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for natural language queries."""

    text: str = Field(..., description="Natural language query text")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "text": "create user with name John and email john@example.com and age 30"
            }
        }


class ActionSchema(BaseModel):
    """Schema for CRUD action."""

    intent: str = Field(..., description="CRUD operation (CREATE, READ, UPDATE, DELETE, SEARCH)")
    resource: Optional[str] = Field(None, description="Resource type (user, order)")
    filters: Dict[str, Any] = Field(default_factory=dict, description="WHERE conditions")
    data: Dict[str, Any] = Field(default_factory=dict, description="Data for INSERT/UPDATE")


class QueryResponse(BaseModel):
    """Response model for query execution."""

    action: ActionSchema = Field(..., description="The executed action")
    result: Dict[str, Any] = Field(..., description="Result of the execution")
    latency_ms: float = Field(..., description="Execution time in milliseconds")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "action": {
                    "intent": "CREATE",
                    "resource": "user",
                    "filters": {},
                    "data": {"name": "John", "email": "john@example.com", "age": 30}
                },
                "result": {
                    "status": "success",
                    "message": "Created in user",
                    "id": 1
                },
                "latency_ms": 15.23
            }
        }


class GenerateSQLRequest(BaseModel):
    """Request model for SQL generation."""

    text: str = Field(..., description="Natural language query text")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "text": "find users older than 30 with gmail accounts"
            }
        }


class GenerateSQLResponse(BaseModel):
    """Response model for SQL generation."""

    action: ActionSchema = Field(..., description="The built action")
    sql: str = Field(..., description="Generated SQL query")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "action": {
                    "intent": "SEARCH",
                    "resource": "user",
                    "filters": {},
                    "data": {"age": 30}
                },
                "sql": "SELECT * FROM users WHERE age > 30"
            }
        }


class SchemaResponse(BaseModel):
    """Response model for schema endpoint."""

    schema: Dict[str, Any] = Field(..., description="Database schema")


class CompareExtractorsRequest(BaseModel):
    """Request model for comparing entity extractors."""

    text: str = Field(..., description="Text to extract entities from")


class CompareExtractorsResponse(BaseModel):
    """Response model for extractor comparison."""

    text: str = Field(..., description="Input text")
    regex_extractor: Dict[str, Any] = Field(..., description="Results from regex extractor")
    spacy_extractor: Dict[str, Any] = Field(..., description="Results from spaCy extractor")


class ErrorResponse(BaseModel):
    """Response model for errors."""

    detail: str = Field(..., description="Error message")
    status: int = Field(..., description="HTTP status code")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "detail": "Failed to build action: No resource specified",
                "status": 400
            }
        }
