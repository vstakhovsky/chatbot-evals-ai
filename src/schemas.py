"""Pydantic schemas for structured outputs across the project."""

from pydantic import BaseModel, Field


class VibeCheckResult(BaseModel):
    """Result of seed vibe check — does this feel like a real support query?"""
    passed: bool = Field(description="True if this could plausibly appear in a real Revolut support queue")
    reasoning: str = Field(description="Concise explanation for the decision")


class SyntheticQuery(BaseModel):
    """Generated synthetic customer query."""
    query: str = Field(description="The customer's message text only")


class VibeCheckValidation(BaseModel):
    """Full validation of a generated query."""
    looks_human_mobile: bool = Field(description="Short, informal, plausibly typed on phone")
    not_ai_slop: bool = Field(description="No assistant-style phrasing, no markdown, no perfect parallelism")
    single_language: bool = Field(description="Message uses only one language throughout")
    matches_problem: bool = Field(description="Addresses the actual user problem described")
    matches_persona: bool = Field(description="Matches the persona's communication style")
    no_pii: bool = Field(description="Contains no real personal information")
    passed: bool = Field(description="Overall pass (AND of all checks)")
    reasoning: str = Field(description="Explanation of failures, or brief confirmation")


class JudgeResult(BaseModel):
    """Binary judge result for a single criterion."""
    passed: bool = Field(description="True if the answer passes this criterion")
    reasoning: str = Field(description="Concise explanation referencing specific evidence")


class GoldLabelResult(BaseModel):
    """Gold label result with richer rubric."""
    gold_passed: bool = Field(description="Gold standard judgment")
    gold_reasoning: str = Field(description="Detailed reasoning following full rubric")
