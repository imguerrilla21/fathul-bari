from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Entity(BaseModel):
    type: str
    value: str

class ResearchQuery(BaseModel):
    original_query: str
    language: str
    intent: str
    entities: List[Entity] = Field(default_factory=list)
    hadith_candidates: List[str] = Field(default_factory=list)
    concepts: List[str] = Field(default_factory=list)
    arabic_terms: List[str] = Field(default_factory=list)
    source_constraints: List[str] = Field(default_factory=list)
    scholar_constraints: List[str] = Field(default_factory=list)
    requested_outputs: List[str] = Field(default_factory=list)

class ResearchPlan(BaseModel):
    steps: List[str]

class ExtractedClaim(BaseModel):
    claim: str
    evidence_ids: List[str] = Field(default_factory=list)

class ClaimsExtractionResult(BaseModel):
    claims: List[ExtractedClaim]

class ResearchAnswerSection(BaseModel):
    title: str
    content: str # Can contain markdown and inline citations like [1]
    claims: List[Dict[str, Any]] = Field(default_factory=list) # Extracted claims for this section

class ResearchAnswerPayload(BaseModel):
    title: str
    summary: str
    sections: List[ResearchAnswerSection]
    uncertainties: List[str] = Field(default_factory=list)
