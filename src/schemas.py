"""Pydantic schemas for validation of generation outputs."""

from pydantic import BaseModel, Field, field_validator
from typing import List


class Persona(BaseModel):
    """Persona schema."""
    persona: str = Field(..., description="Persona ID")
    age: int
    region: str
    plan_products: str
    english: str = Field(..., pattern="^(basic|fluent|native)$")
    description: str


class Modifier(BaseModel):
    """Modifier schema."""
    modifier: str = Field(..., description="Modifier ID")
    description: str
    style_instructions: str


class Scenario(BaseModel):
    """Scenario schema."""
    persona: str
    scenario: str = Field(..., description="Scenario ID")
    intent_summary: str
    target_articles: List[str] = Field(..., min_length=2, max_length=5)


class GeneratedQuery(BaseModel):
    """Generated query output schema."""
    query: str = Field(..., min_length=5, max_length=500)

    @field_validator('query')
    def query_must_be_realistic(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        # Basic sanity checks
        if v.lower().startswith("hello") or v.lower().startswith("hi "):
            if len(v) < 20:
                raise ValueError("Query cannot be just a greeting")
        return v


class GenerationRequest(BaseModel):
    """Request for query generation."""
    persona_description: str
    english_level: str
    scenario_intent: str
    target_articles: List[str]
    modifier_instructions: str
