from typing import Dict, Any, List, Optional
import decimal
import re
import logging
from src.core.validation_rules import ValidationEngine

logger = logging.getLogger(__name__)

class ValidationService:
    def __init__(self):
        self.validation_engine = ValidationEngine()
        logger.info("Validation Service initialized")
    
    def validate_template(
        self, 
        template_data: Dict[str, Any],
        template_id: str,
        regulatory_texts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Validate populated template data against rules."""
        
        from src.config.corep_templates import COREP_TEMPLATES
        
        logger.info(f"Starting validation for template {template_id}")
        
        template = COREP_TEMPLATES.get(template_id)
        if not template:
            logger.error(f"Template {template_id} not found")
            return {
                "valid": False,
                "errors": [{"message": f"Template {template_id} not found"}],
                "warnings": [],
                "checks_performed": 0
            }
        
        # Use the validation engine
        validation_results = self.validation_engine.validate_template(
            template_data, template_id
        )
        
        # Add regulatory validation if texts provided
        if regulatory_texts:
            regulatory_violations = self._validate_against_regulatory_rules(
                template_data, regulatory_texts
            )
            
            if regulatory_violations:
                validation_results["rule_violations"] = regulatory_violations
                
                for violation in regulatory_violations:
                    if not violation.get("valid", True):
                        validation_results["valid"] = False
                        validation_results["errors"].append({
                            "field": violation.get("field", "unknown"),
                            "message": f"Regulatory violation: {violation.get('message')}",
                            "rule_id": violation.get("rule_id", "REG_001"),
                            "severity": "error"
                        })
        
        # Log summary
        logger.info(f"Validation complete: {len(validation_results['errors'])} errors, {len(validation_results['warnings'])} warnings")
        
        return validation_results
    
    def _validate_against_regulatory_rules(
        self,
        template_data: Dict[str, Any],
        regulatory_texts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate data against specific regulatory rules."""
        violations = []
        
        logger.info(f"Validating against {len(regulatory_texts)} regulatory rules")
        
        for text in regulatory_texts:
            metadata = text.get("metadata", {})
            validation_rules = metadata.get("validation_rules", [])
            paragraph_id = metadata.get("paragraph_id", "")
            
            if not validation_rules:
                continue
            
            field_refs = metadata.get("field_references", [])
            logger.debug(f"Rule {paragraph_id}: {len(validation_rules)} validations, fields: {field_refs}")
            
            for rule in validation_rules:
                if rule == "positive_decimal":
                    self._validate_positive_decimal(
                        template_data, field_refs, paragraph_id, violations
                    )
                
                elif rule.startswith("equals_sum:"):
                    self._validate_equals_sum(
                        template_data, field_refs, rule, paragraph_id, violations
                    )
                
                elif rule == "required":
                    self._validate_required(
                        template_data, field_refs, paragraph_id, violations
                    )
                
                elif rule.startswith("range:"):
                    self._validate_range(
                        template_data, field_refs, rule, paragraph_id, violations
                    )
        
        logger.info(f"Found {len(violations)} regulatory violations")
        return violations
    
    def _validate_positive_decimal(
        self,
        template_data: Dict[str, Any],
        field_refs: List[str],
        paragraph_id: str,
        violations: List[Dict[str, Any]]
    ):
        """Validate that fields are positive decimals."""
        for field_id in field_refs:
            if field_id in template_data:
                value_data = template_data[field_id]
                value = value_data.get("value") if isinstance(value_data, dict) else value_data
                
                try:
                    if isinstance(value, str):
                        value_str = value.replace(',', '').replace('£', '').replace('$', '').strip()
                    else:
                        value_str = str(value)
                    
                    decimal_value = decimal.Decimal(value_str)
                    
                    if decimal_value < 0:
                        violations.append({
                            "field": field_id,
                            "message": f"Field must be positive per {paragraph_id}",
                            "rule_id": paragraph_id,
                            "valid": False,
                            "severity": "error"
                        })
                        logger.warning(f"Field {field_id} negative: {value}")
                        
                except (decimal.InvalidOperation, ValueError):
                    violations.append({
                        "field": field_id,
                        "message": f"Field is not a valid decimal per {paragraph_id}",
                        "rule_id": paragraph_id,
                        "valid": False,
                        "severity": "error"
                    })
    
    def _validate_equals_sum(
        self,
        template_data: Dict[str, Any],
        field_refs: List[str],
        rule_spec: str,
        paragraph_id: str,
        violations: List[Dict[str, Any]]
    ):
        """Validate that a field equals sum of other fields."""
        try:
            # Parse formula like "equals_sum:r010+r020+r030"
            formula = rule_spec.replace("equals_sum:", "")
            sum_fields = formula.split('+')
            
            total = decimal.Decimal('0')
            
            for field_ref in sum_fields:
                # Find the actual field ID
                actual_field_id = None
                for template_field in template_data:
                    if field_ref in template_field:
                        actual_field_id = template_field
                        break
                
                if actual_field_id and actual_field_id in template_data:
                    value_data = template_data[actual_field_id]
                    value = value_data.get("value") if isinstance(value_data, dict) else value_data
                    
                    if isinstance(value, str):
                        value_str = value.replace(',', '').replace('£', '').replace('$', '').strip()
                    else:
                        value_str = str(value)
                    
                    total += decimal.Decimal(value_str)
            
            # Check which field should equal the sum
            for field_id in field_refs:
                if field_id in template_data:
                    value_data = template_data[field_id]
                    value = value_data.get("value") if isinstance(value_data, dict) else value_data
                    
                    if isinstance(value, str):
                        value_str = value.replace(',', '').replace('£', '').replace('$', '').strip()
                    else:
                        value_str = str(value)
                    
                    field_value = decimal.Decimal(value_str)
                    
                    if field_value != total:
                        violations.append({
                            "field": field_id,
                            "message": f"Field must equal sum of {formula} per {paragraph_id}",
                            "rule_id": paragraph_id,
                            "valid": False,
                            "severity": "error",
                            "expected": str(total),
                            "actual": str(field_value)
                        })
                        logger.warning(f"Field {field_id} sum mismatch: {field_value} != {total}")
                        
        except Exception as e:
            logger.warning(f"Could not validate sum rule {paragraph_id}: {e}")
    
    def _validate_required(
        self,
        template_data: Dict[str, Any],
        field_refs: List[str],
        paragraph_id: str,
        violations: List[Dict[str, Any]]
    ):
        """Validate that required fields are present."""
        for field_id in field_refs:
            if field_id not in template_data:
                violations.append({
                    "field": field_id,
                    "message": f"Required field missing per {paragraph_id}",
                    "rule_id": paragraph_id,
                    "valid": False,
                    "severity": "error"
                })
                logger.warning(f"Required field missing: {field_id}")
    
    def _validate_range(
        self,
        template_data: Dict[str, Any],
        field_refs: List[str],
        rule_spec: str,
        paragraph_id: str,
        violations: List[Dict[str, Any]]
    ):
        """Validate that fields are within range."""
        try:
            # Parse range like "range:0-2"
            range_str = rule_spec.replace("range:", "")
            if '-' in range_str:
                min_val, max_val = map(float, range_str.split('-'))
            else:
                logger.warning(f"Invalid range format: {rule_spec}")
                return
            
            for field_id in field_refs:
                if field_id in template_data:
                    value_data = template_data[field_id]
                    value = value_data.get("value") if isinstance(value_data, dict) else value_data
                    
                    if isinstance(value, str):
                        # Remove percentage sign if present
                        value_str = value.replace('%', '').replace(',', '').strip()
                    else:
                        value_str = str(value)
                    
                    try:
                        numeric_value = float(value_str)
                        
                        if numeric_value < min_val or numeric_value > max_val:
                            violations.append({
                                "field": field_id,
                                "message": f"Field must be between {min_val} and {max_val} per {paragraph_id}",
                                "rule_id": paragraph_id,
                                "valid": False,
                                "severity": "error",
                                "min": min_val,
                                "max": max_val,
                                "actual": numeric_value
                            })
                            logger.warning(f"Field {field_id} out of range: {numeric_value} not in [{min_val}, {max_val}]")
                            
                    except ValueError:
                        violations.append({
                            "field": field_id,
                            "message": f"Field is not a valid number per {paragraph_id}",
                            "rule_id": paragraph_id,
                            "valid": False,
                            "severity": "error"
                        })
                        
        except Exception as e:
            logger.warning(f"Could not validate range rule {paragraph_id}: {e}")