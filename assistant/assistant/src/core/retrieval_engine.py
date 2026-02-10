from typing import Any, Dict, List, Optional
import decimal
import re
import logging

logger = logging.getLogger(__name__)

class ValidationRule:
    """Base class for validation rules."""
    
    def __init__(self, rule_id: str, description: str, severity: str = "error"):
        self.rule_id = rule_id
        self.description = description
        self.severity = severity
    
    def validate(self, value: Any, field_id: str = None) -> Dict[str, Any]:
        """Validate a value and return result."""
        raise NotImplementedError

class PositiveDecimalRule(ValidationRule):
    """Validate that a value is a positive decimal."""
    
    def __init__(self):
        super().__init__(
            rule_id="POSITIVE_DECIMAL",
            description="Value must be a positive decimal number",
            severity="error"
        )
    
    def validate(self, value: Any, field_id: str = None) -> Dict[str, Any]:
        try:
            # Clean value string
            if isinstance(value, str):
                value_str = value.replace(',', '').replace('£', '').replace('$', '').strip()
            else:
                value_str = str(value)
            
            # Convert to decimal
            decimal_value = decimal.Decimal(value_str)
            
            if decimal_value < 0:
                return {
                    "valid": False,
                    "message": f"Field {field_id} must be positive, got {value}",
                    "severity": self.severity,
                    "rule_id": self.rule_id
                }
            
            return {
                "valid": True,
                "message": f"Field {field_id} is positive",
                "severity": self.severity,
                "rule_id": self.rule_id
            }
            
        except (decimal.InvalidOperation, ValueError):
            return {
                "valid": False,
                "message": f"Field {field_id} is not a valid decimal: {value}",
                "severity": self.severity,
                "rule_id": self.rule_id
            }

class DecimalPlacesRule(ValidationRule):
    """Validate that a decimal has specified number of decimal places."""
    
    def __init__(self, decimal_places: int = 2):
        super().__init__(
            rule_id=f"DECIMAL_PLACES_{decimal_places}",
            description=f"Value must have exactly {decimal_places} decimal places",
            severity="warning"
        )
        self.decimal_places = decimal_places
    
    def validate(self, value: Any, field_id: str = None) -> Dict[str, Any]:
        try:
            if isinstance(value, str):
                value_str = value.replace(',', '').strip()
            else:
                value_str = str(value)
            
            decimal_value = decimal.Decimal(value_str)
            actual_places = abs(decimal_value.as_tuple().exponent)
            
            if actual_places != self.decimal_places:
                return {
                    "valid": False,
                    "message": f"Field {field_id} should have {self.decimal_places} decimal places, got {actual_places}",
                    "severity": self.severity,
                    "rule_id": self.rule_id
                }
            
            return {
                "valid": True,
                "message": f"Field {field_id} has correct decimal places",
                "severity": self.severity,
                "rule_id": self.rule_id
            }
            
        except (decimal.InvalidOperation, ValueError):
            return {
                "valid": False,
                "message": f"Field {field_id} is not a valid decimal",
                "severity": self.severity,
                "rule_id": self.rule_id
            }

class RangeRule(ValidationRule):
    """Validate that a value is within a specified range."""
    
    def __init__(self, min_value: float = None, max_value: float = None):
        description = "Value must be within range"
        if min_value is not None and max_value is not None:
            description = f"Value must be between {min_value} and {max_value}"
        elif min_value is not None:
            description = f"Value must be at least {min_value}"
        elif max_value is not None:
            description = f"Value must be at most {max_value}"
        
        super().__init__(
            rule_id="RANGE_VALIDATION",
            description=description,
            severity="error"
        )
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any, field_id: str = None) -> Dict[str, Any]:
        try:
            if isinstance(value, str):
                # Remove percentage sign if present
                value_str = value.replace('%', '').replace(',', '').strip()
            else:
                value_str = str(value)
            
            numeric_value = float(value_str)
            
            if self.min_value is not None and numeric_value < self.min_value:
                return {
                    "valid": False,
                    "message": f"Field {field_id} must be at least {self.min_value}, got {value}",
                    "severity": self.severity,
                    "rule_id": self.rule_id
                }
            
            if self.max_value is not None and numeric_value > self.max_value:
                return {
                    "valid": False,
                    "message": f"Field {field_id} must be at most {self.max_value}, got {value}",
                    "severity": self.severity,
                    "rule_id": self.rule_id
                }
            
            return {
                "valid": True,
                "message": f"Field {field_id} is within valid range",
                "severity": self.severity,
                "rule_id": self.rule_id
            }
            
        except ValueError:
            return {
                "valid": False,
                "message": f"Field {field_id} is not a valid number: {value}",
                "severity": self.severity,
                "rule_id": self.rule_id
            }

class RequiredFieldRule(ValidationRule):
    """Validate that a required field is present."""
    
    def __init__(self):
        super().__init__(
            rule_id="REQUIRED_FIELD",
            description="Required field must be present and non-empty",
            severity="error"
        )
    
    def validate(self, value: Any, field_id: str = None) -> Dict[str, Any]:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return {
                "valid": False,
                "message": f"Required field {field_id} is missing or empty",
                "severity": self.severity,
                "rule_id": self.rule_id
            }
        
        return {
            "valid": True,
            "message": f"Required field {field_id} is present",
            "severity": self.severity,
            "rule_id": self.rule_id
        }

class SumEqualsRule(ValidationRule):
    """Validate that a field equals the sum of other fields."""
    
    def __init__(self, sum_fields: List[str], target_field: str):
        super().__init__(
            rule_id="SUM_EQUALS",
            description=f"Field must equal sum of {', '.join(sum_fields)}",
            severity="error"
        )
        self.sum_fields = sum_fields
        self.target_field = target_field
    
    def validate(self, data: Dict[str, Any], field_id: str = None) -> Dict[str, Any]:
        try:
            # Calculate sum
            total = decimal.Decimal('0')
            for field in self.sum_fields:
                if field in data:
                    value = data[field]
                    if isinstance(value, dict):
                        value = value.get('value', '0')
                    
                    # Clean value
                    if isinstance(value, str):
                        value_str = value.replace(',', '').replace('£', '').replace('$', '').strip()
                    else:
                        value_str = str(value)
                    
                    total += decimal.Decimal(value_str)
            
            # Get target value
            target_value = data.get(self.target_field)
            if isinstance(target_value, dict):
                target_value = target_value.get('value', '0')
            
            if isinstance(target_value, str):
                target_str = target_value.replace(',', '').replace('£', '').replace('$', '').strip()
            else:
                target_str = str(target_value)
            
            target_decimal = decimal.Decimal(target_str)
            
            if target_decimal != total:
                return {
                    "valid": False,
                    "message": f"Field {self.target_field} ({target_decimal}) does not equal sum {total}",
                    "severity": self.severity,
                    "rule_id": self.rule_id
                }
            
            return {
                "valid": True,
                "message": f"Field {self.target_field} equals sum of {', '.join(self.sum_fields)}",
                "severity": self.severity,
                "rule_id": self.rule_id
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Sum validation failed: {str(e)}",
                "severity": self.severity,
                "rule_id": self.rule_id
            }

class ValidationEngine:
    """Main validation engine that applies all rules."""
    
    def __init__(self):
        self.rules = {
            "positive_decimal": PositiveDecimalRule(),
            "decimal_places:2": DecimalPlacesRule(2),
            "required": RequiredFieldRule()
        }
    
    def validate_field(self, field_id: str, value: Any, validation_spec: List[str]) -> List[Dict[str, Any]]:
        """Validate a single field against its validation spec."""
        results = []
        
        for rule_spec in validation_spec:
            if rule_spec in self.rules:
                rule = self.rules[rule_spec]
                result = rule.validate(value, field_id)
                results.append(result)
            
            elif rule_spec.startswith("range:"):
                # Parse range like "range:0-2"
                range_str = rule_spec.replace("range:", "")
                if '-' in range_str:
                    min_val, max_val = map(float, range_str.split('-'))
                    rule = RangeRule(min_val, max_val)
                    result = rule.validate(value, field_id)
                    results.append(result)
            
            elif rule_spec.startswith("decimal_places:"):
                # Parse decimal places like "decimal_places:2"
                places = int(rule_spec.split(':')[1])
                rule = DecimalPlacesRule(places)
                result = rule.validate(value, field_id)
                results.append(result)
        
        return results
    
    def validate_template(self, template_data: Dict[str, Any], template_id: str) -> Dict[str, Any]:
        """Validate all fields in a template."""
        from src.config.corep_templates import COREP_TEMPLATES
        
        template = COREP_TEMPLATES.get(template_id)
        if not template:
            return {
                "valid": False,
                "errors": [{"message": f"Template {template_id} not found"}],
                "warnings": []
            }
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "field_validations": {},
            "template_validations": []
        }
        
        # Validate each field
        for field_id, field_info in template["fields"].items():
            if field_id in template_data:
                value_data = template_data[field_id]
                value = value_data.get("value") if isinstance(value_data, dict) else value_data
                
                # Get validation rules for this field
                validation_spec = field_info.get("validation", [])
                
                if validation_spec:
                    field_results = self.validate_field(field_id, value, validation_spec)
                    validation_results["field_validations"][field_id] = field_results
                    
                    for result in field_results:
                        if not result["valid"]:
                            if result["severity"] == "error":
                                validation_results["valid"] = False
                                validation_results["errors"].append({
                                    "field": field_id,
                                    "message": result["message"],
                                    "rule_id": result["rule_id"],
                                    "severity": "error"
                                })
                            else:
                                validation_results["warnings"].append({
                                    "field": field_id,
                                    "message": result["message"],
                                    "rule_id": result["rule_id"],
                                    "severity": "warning"
                                })
        
        # Validate template-level rules
        for rule in template.get("validation_rules", []):
            if rule.get("condition"):
                try:
                    # Simple condition evaluation
                    condition = rule["condition"]
                    
                    # Replace field references with values
                    for field_id, field_data in template_data.items():
                        if field_id in condition:
                            value = field_data.get("value") if isinstance(field_data, dict) else field_data
                            if isinstance(value, str):
                                # Extract numeric value
                                import re
                                numbers = re.findall(r'[\d\.]+', value)
                                if numbers:
                                    value = float(numbers[0].replace(',', ''))
                                else:
                                    value = 0
                            condition = condition.replace(field_id, str(value))
                    
                    # Evaluate condition
                    if not eval(condition, {"__builtins__": {}}):
                        validation_results["template_validations"].append({
                            "rule_id": rule.get("rule_id"),
                            "valid": False,
                            "message": rule.get("description"),
                            "severity": rule.get("severity", "error")
                        })
                        
                        if rule.get("severity") == "error":
                            validation_results["valid"] = False
                            validation_results["errors"].append({
                                "field": "template",
                                "message": rule.get("description"),
                                "rule_id": rule.get("rule_id"),
                                "severity": "error"
                            })
                        else:
                            validation_results["warnings"].append({
                                "field": "template",
                                "message": rule.get("description"),
                                "rule_id": rule.get("rule_id"),
                                "severity": "warning"
                            })
                    else:
                        validation_results["template_validations"].append({
                            "rule_id": rule.get("rule_id"),
                            "valid": True,
                            "message": f"Passed: {rule.get('description')}",
                            "severity": rule.get("severity", "error")
                        })
                        
                except Exception as e:
                    logger.warning(f"Could not evaluate template rule: {e}")
        
        logger.info(f"Validation completed: {len(validation_results['errors'])} errors, {len(validation_results['warnings'])} warnings")
        return validation_results