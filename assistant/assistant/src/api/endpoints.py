from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

class ReportingRequest(BaseModel):
    question: str
    scenario: Optional[str] = None
    template_id: str = "C_01.00"
    bank_size: Optional[str] = None

@router.post("/report")
async def generate_report(request: ReportingRequest):
    """Generate COREP report based on natural language query."""
    logger.info(f"Processing report request: template={request.template_id}")
    
    try:
        # Try to use the real reporting service if available
        from src.services.reporting_service import ReportingService
        reporting_service = ReportingService()
        response = await reporting_service.process_reporting_request(request)
        return response
        
    except ImportError:
        logger.warning("ReportingService not available, returning enhanced mock data")
        # Return enhanced mock response
        return generate_enhanced_mock_response(request)
        
    except Exception as e:
        logger.error(f"Error in ReportingService: {e}")
        # Fall back to mock data if real service fails
        return generate_enhanced_mock_response(request)

def generate_enhanced_mock_response(request: ReportingRequest):
    """Generate enhanced mock response for demonstration."""
    
    # Parse the question to extract amounts (simple regex for demo)
    amounts = re.findall(r'£\s*([\d,.]+)\s*million', request.question.lower())
    if amounts:
        base_amount = float(amounts[0].replace(',', '')) * 1000000
    else:
        amounts = re.findall(r'£\s*([\d,.]+)', request.question.lower())
        if amounts:
            try:
                base_amount = float(amounts[0].replace(',', ''))
            except ValueError:
                base_amount = 1500000  # Default
        else:
            base_amount = 1500000  # Default
    
    # Generate mock data based on template
    if request.template_id == "C_01.00":
        populated_fields = {
            "C_01.00_r010_c010": {
                "value": f"{base_amount:,.2f}",
                "confidence": 0.95,
                "reasoning": "Common Equity Tier 1 includes capital instruments and retained earnings as per PRA Rulebook 4.2.1",
                "regulatory_references": ["PRA_RB_4.2.1"]
            },
            "C_01.00_r020_c010": {
                "value": f"{base_amount * 0.3:,.2f}",
                "confidence": 0.88,
                "reasoning": "Additional Tier 1 capital calculated as 30% of CET1 based on qualifying instruments",
                "regulatory_references": ["PRA_RB_4.2.5"]
            },
            "C_01.00_r030_c010": {
                "value": f"{base_amount * 0.5:,.2f}",
                "confidence": 0.92,
                "reasoning": "Tier 2 capital calculation per PRA guidelines for standardised approach",
                "regulatory_references": ["PRA_RB_4.2.8"]
            }
        }
        
        # Calculate total
        total = base_amount + (base_amount * 0.3) + (base_amount * 0.5)
        populated_fields["C_01.00_r040_c010"] = {
            "value": f"{total:,.2f}",
            "confidence": 0.98,
            "reasoning": "Total eligible capital = CET1 + AT1 + T2",
            "regulatory_references": ["PRA_RB_4.2.1", "PRA_RB_4.2.5", "PRA_RB_4.2.8"]
        }
        
    else:
        # Default mock data for other templates
        populated_fields = {
            f"{request.template_id}_r010_c010": {
                "value": "1000000.00",
                "confidence": 0.85,
                "reasoning": "Based on regulatory requirements for capital adequacy",
                "regulatory_references": ["PRA_RB_4.3.1"]
            }
        }
    
    return {
        "session_id": f"demo-{int(datetime.now().timestamp())}",
        "template_id": request.template_id,
        "populated_fields": populated_fields,
        "template_output": {
            "template_id": request.template_id,
            "name": "Own Funds" if request.template_id == "C_01.00" else "Capital Requirements",
            "description": "COREP regulatory reporting template",
            "fields": [
                {
                    "field_id": field_id,
                    "field_name": field_data.get("reasoning", "").split(" ")[0] if "reasoning" in field_data else field_id,
                    "value": field_data.get("value", ""),
                    "confidence": field_data.get("confidence", 0)
                }
                for field_id, field_data in populated_fields.items()
            ]
        },
        "audit_trail": {
            field_id: data.get("regulatory_references", [])
            for field_id, data in populated_fields.items()
        },
        "validation_results": {
            "valid": True,
            "errors": [],
            "warnings": [
                {
                    "field": list(populated_fields.keys())[1] if len(populated_fields) > 1 else list(populated_fields.keys())[0],
                    "message": "Confidence score below 90%",
                    "severity": "warning"
                }
            ] if len(populated_fields) > 1 else [],
            "checks_performed": len(populated_fields) * 2
        },
        "relevant_regulations": [
            {
                "content": "Common Equity Tier 1 capital shall consist of the sum of the following elements: (a) capital instruments and related share premium accounts that meet the criteria for classification as common equity tier 1 capital instruments; (b) retained earnings; (c) accumulated other comprehensive income; (d) other reserves; minus the applicable regulatory adjustments.",
                "metadata": {
                    "paragraph_id": "PRA_RB_4.2.1",
                    "source": "PRA Rulebook",
                    "section": "Own Funds",
                    "template_reference": "C_01.00"
                },
                "similarity_score": 0.95
            },
            {
                "content": "Additional Tier 1 capital shall consist of capital instruments that meet the criteria for classification as additional tier 1 capital instruments, plus any related share premium accounts, minus the applicable regulatory adjustments.",
                "metadata": {
                    "paragraph_id": "PRA_RB_4.2.5",
                    "source": "PRA Rulebook",
                    "section": "Own Funds",
                    "template_reference": "C_01.00"
                },
                "similarity_score": 0.88
            }
        ],
        "timestamp": datetime.now().isoformat(),
        "confidence_score": 0.91,
        "processing_time_ms": 1875,
        "message": "Mock response - Configure Grok API for real LLM processing"
    }

@router.get("/templates")
async def list_templates():
    """List available COREP templates."""
    return {
        "templates": [
            {
                "id": "C_01.00",
                "name": "Own Funds",
                "description": "Template for reporting own funds and eligible capital",
                "fields": [
                    {"id": "C_01.00_r010_c010", "name": "Common Equity Tier 1 capital", "required": True},
                    {"id": "C_01.00_r020_c010", "name": "Additional Tier 1 capital", "required": True},
                    {"id": "C_01.00_r030_c010", "name": "Tier 2 capital", "required": True},
                    {"id": "C_01.00_r040_c010", "name": "Total eligible capital", "required": True}
                ]
            },
            {
                "id": "C_02.00", 
                "name": "Capital Requirements",
                "description": "Template for reporting capital requirements",
                "fields": [
                    {"id": "C_02.00_r010_c010", "name": "Credit risk", "required": True},
                    {"id": "C_02.00_r020_c010", "name": "Market risk", "required": True},
                    {"id": "C_02.00_r030_c010", "name": "Operational risk", "required": True}
                ]
            },
            {
                "id": "C_03.00",
                "name": "Credit Risk",
                "description": "Template for reporting credit risk exposures",
                "fields": [
                    {"id": "C_03.00_r010_c010", "name": "Exposures to central governments", "required": True},
                    {"id": "C_03.00_r020_c010", "name": "Exposures to institutions", "required": True},
                    {"id": "C_03.00_r030_c010", "name": "Exposures to corporates", "required": True}
                ]
            }
        ]
    }

@router.get("/regulations/search")
async def search_regulations(query: str, limit: int = 5):
    """Search regulatory texts."""
    # Mock search results
    return {
        "query": query,
        "results": [
            {
                "content": "Common Equity Tier 1 capital shall consist of the sum of the following elements...",
                "metadata": {
                    "paragraph_id": "PRA_RB_4.2.1",
                    "source": "PRA Rulebook",
                    "section": "Own Funds",
                    "template_reference": "C_01.00"
                },
                "similarity_score": 0.95
            },
            {
                "content": "Institutions shall hold own funds which are at all times more than or equal to the following: (a) Common Equity Tier 1 capital ratio of 4.5%; (b) Tier 1 capital ratio of 6%; (c) Total capital ratio of 8%.",
                "metadata": {
                    "paragraph_id": "PRA_RB_4.3.1",
                    "source": "PRA Rulebook", 
                    "section": "Capital Requirements",
                    "template_reference": "C_02.00"
                },
                "similarity_score": 0.87
            }
        ]
    }