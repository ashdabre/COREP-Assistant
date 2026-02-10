from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class RegulatoryTextResponse(BaseModel):
    """Response schema for regulatory text."""
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    distance: Optional[float] = None

class FieldValue(BaseModel):
    """Schema for field value with metadata."""
    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    regulatory_references: List[str] = Field(default_factory=list)
    data_type: Optional[str] = None
    required: Optional[bool] = None

class ValidationResult(BaseModel):
    """Schema for validation result."""
    valid: bool
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)
    checks_performed: int = 0
    rule_violations: List[Dict[str, Any]] = Field(default_factory=list)
    field_validations: Optional[Dict[str, Any]] = None
    template_validations: Optional[List[Dict[str, Any]]] = None

class ReportingResponse(BaseModel):
    """Response schema for reporting requests."""
    session_id: str
    template_id: str
    populated_fields: Dict[str, Any]
    template_output: Dict[str, Any]
    audit_trail: Dict[str, List[str]]
    validation_results: ValidationResult
    relevant_regulations: List[RegulatoryTextResponse]
    timestamp: datetime
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: int
    message: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "123e4567-e89b-12d3-a456-426614174000",
                "template_id": "C_01.00",
                "populated_fields": {
                    "C_01.00_r010_c010": {
                        "value": "1,500,000.00",
                        "confidence": 0.95,
                        "reasoning": "Based on PRA_RB_4.2.1",
                        "regulatory_references": ["PRA_RB_4.2.1"]
                    }
                },
                "timestamp": "2023-01-01T00:00:00Z",
                "confidence_score": 0.9,
                "processing_time_ms": 1250,
                "message": "Report generated successfully"
            }
        }