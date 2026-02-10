from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class TemplateEnum(str, Enum):
    """Supported COREP templates."""
    OWN_FUNDS = "C_01.00"
    CAPITAL_REQUIREMENTS = "C_02.00"

class ReportingRequest(BaseModel):
    """Request schema for generating COREP reports."""
    
    question: str = Field(
        ...,
        description="Natural language question about regulatory reporting",
        example="What is Common Equity Tier 1 capital for a bank with £2 million in qualifying instruments?"
    )
    
    scenario: Optional[str] = Field(
        None,
        description="Additional context about the reporting scenario",
        example="UK retail bank, standardised approach, consolidated basis"
    )
    
    template_id: TemplateEnum = Field(
        ...,
        description="COREP template to populate",
        example="C_01.00"
    )
    
    retrieval_count: Optional[int] = Field(
        3,
        description="Number of regulatory rules to retrieve",
        ge=1,
        le=10
    )
    
    confidence_threshold: Optional[float] = Field(
        0.7,
        description="Minimum similarity threshold for rule retrieval",
        ge=0.0,
        le=1.0
    )
    
    class Config:
        schema_extra = {
            "example": {
                "question": "Calculate CET1 capital for a bank with £1.5M instruments and £500k retained earnings",
                "scenario": "UK building society, standardised approach",
                "template_id": "C_01.00",
                "retrieval_count": 3,
                "confidence_threshold": 0.7
            }
        }