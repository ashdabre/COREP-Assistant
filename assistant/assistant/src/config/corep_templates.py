COREP_TEMPLATES = {
    "C_01.00": {
        "name": "Own Funds (Capital)",
        "description": "Template for reporting own funds components: CET1, AT1, Tier 2, and total eligible capital as per PRA Rulebook 4.2",
        "version": "1.0",
        "effective_date": "2023-01-01",
        "fields": {
            "C_01.00_r010_c010": {
                "name": "Common Equity Tier 1 (CET1) capital",
                "description": "Core capital including common shares, retained earnings, and other reserves",
                "data_type": "decimal",
                "format": "##,###,##0.00",
                "required": True,
                "validation": ["positive_decimal", "decimal_places:2", "required"],
                "regulatory_reference": "PRA_RB_4.2.1"
            },
            "C_01.00_r020_c010": {
                "name": "Additional Tier 1 (AT1) capital",
                "description": "Additional capital instruments that are perpetual and subordinated",
                "data_type": "decimal",
                "format": "##,###,##0.00",
                "required": True,
                "validation": ["positive_decimal", "decimal_places:2", "required"],
                "regulatory_reference": "PRA_RB_4.2.5"
            },
            "C_01.00_r030_c010": {
                "name": "Tier 2 capital",
                "description": "Supplementary capital with minimum 5-year maturity",
                "data_type": "decimal",
                "format": "##,###,##0.00",
                "required": True,
                "validation": ["positive_decimal", "decimal_places:2", "required"],
                "regulatory_reference": "PRA_RB_4.2.8"
            },
            "C_01.00_r040_c010": {
                "name": "Total eligible capital (Own Funds)",
                "description": "Sum of CET1, AT1, and Tier 2 capital after regulatory adjustments",
                "data_type": "decimal",
                "format": "##,###,##0.00",
                "required": True,
                "validation": ["positive_decimal", "decimal_places:2", "required", "equals_sum:C_01.00_r010_c010+C_01.00_r020_c010+C_01.00_r030_c010"],
                "regulatory_reference": "PRA_RB_4.2.12"
            }
        },
        "validation_rules": [
            {
                "rule_id": "VAL_001",
                "condition": "C_01.00_r040_c010 == C_01.00_r010_c010 + C_01.00_r020_c010 + C_01.00_r030_c010",
                "description": "Total eligible capital must equal sum of CET1, AT1, and Tier 2 capital",
                "severity": "error",
                "regulatory_reference": "PRA_RB_4.2.12"
            }
        ]
    },
    "C_02.00": {
        "name": "Capital Requirements",
        "description": "Template for reporting capital requirements and buffers as per PRA Rulebook 4.3",
        "version": "1.0",
        "effective_date": "2023-01-01",
        "fields": {
            "C_02.00_r010_c010": {
                "name": "Minimum CET1 ratio requirement",
                "description": "Minimum Common Equity Tier 1 capital ratio (4.5%)",
                "data_type": "percentage",
                "format": "0.00%",
                "required": True,
                "validation": ["decimal", "range:4.5-100", "decimal_places:2"],
                "regulatory_reference": "PRA_RB_4.3.1"
            },
            "C_02.00_r020_c010": {
                "name": "Minimum Tier 1 ratio requirement",
                "description": "Minimum Tier 1 capital ratio (6%)",
                "data_type": "percentage",
                "format": "0.00%",
                "required": True,
                "validation": ["decimal", "range:6-100", "decimal_places:2"],
                "regulatory_reference": "PRA_RB_4.3.1"
            },
            "C_02.00_r030_c010": {
                "name": "Minimum Total capital ratio requirement",
                "description": "Minimum Total capital ratio (8%)",
                "data_type": "percentage",
                "format": "0.00%",
                "required": True,
                "validation": ["decimal", "range:8-100", "decimal_places:2"],
                "regulatory_reference": "PRA_RB_4.3.1"
            },
            "C_02.00_r040_c010": {
                "name": "Capital conservation buffer",
                "description": "Capital conservation buffer requirement (2.5%)",
                "data_type": "percentage",
                "format": "0.00%",
                "required": True,
                "validation": ["decimal", "range:2.5-100", "decimal_places:2"],
                "regulatory_reference": "PRA_RB_4.3.5"
            }
        },
        "validation_rules": []
    }
}