"""Pydantic schemas for validation of generation outputs."""

from pydantic import BaseModel, Field, field_validator


class GeneratedQuery(BaseModel):
    """Generated query output schema."""
    query: str = Field(..., min_length=5, max_length=500)

    @field_validator('query')
    def query_must_be_realistic(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        # Basic sanity checks
        if (
            (v.lower().startswith("hello") or v.lower().startswith("hi ")) and
            len(v) < 20
        ):
            raise ValueError("Query cannot be just a greeting")
        return v
