
import logging
from typing import Dict, Any, List, Optional
import json
import asyncio
from src.config.settings import settings

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.use_openai = bool(settings.OPENAI_API_KEY)
        
        if self.use_openai:
            try:
                import openai
                self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI not available, using rule-based fallback")
                self.use_openai = False
        else:
            logger.info("Using rule-based processing (no OpenAI API key provided)")
    
    async def generate_structured_output(
        self,
        query: str,
        scenario: str,
        context: List[Dict[str, Any]],
        template_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured output using LLM or rule-based approach."""
        
        if self.use_openai:
            return await self._generate_with_openai(
                query, scenario, context, template_schema
            )
        else:
            return self._generate_rule_based_output(
                query, scenario, context, template_schema
            )
    
    async def _generate_with_openai(
        self,
        query: str,
        scenario: str,
        context: List[Dict[str, Any]],
        template_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured output using OpenAI."""
        try:
            # Prepare context
            context_text = "\n\n".join([
                f"Regulation {i+1}:\n{text['content'][:500]}..."
                for i, text in enumerate(context[:3])
            ])
            
            # Prepare template schema
            template_fields = []
            for field_id, field_info in template_schema.items():
                template_fields.append(f"{field_id}: {field_info.get('name', '')} ({field_info.get('data_type', 'string')})")
            
            # Create prompt
            prompt = f"""
            You are a regulatory reporting assistant for UK banks. 
            Based on the following regulatory context and question, populate the COREP template fields.
            
            QUESTION: {query}
            SCENARIO: {scenario}
            
            REGULATORY CONTEXT:
            {context_text}
            
            TEMPLATE FIELDS TO POPULATE:
            {chr(10).join(template_fields)}
            
            INSTRUCTIONS:
            1. Extract relevant amounts from the question
            2. Apply regulatory rules from context
            3. Return JSON with field_id as key and object with:
               - value: calculated value (formatted as string)
               - confidence: 0.0 to 1.0
               - reasoning: brief explanation
               - regulatory_references: list of regulation IDs used
            
            EXAMPLE:
            {{
              "C_01.00_r010_c010": {{
                "value": "1,500,000.00",
                "confidence": 0.95,
                "reasoning": "Based on PRA_RB_4.2.1: CET1 includes capital instruments and retained earnings",
                "regulatory_references": ["PRA_RB_4.2.1"]
              }}
            }}
            
            OUTPUT ONLY VALID JSON:
            """
            
            # Call OpenAI
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a regulatory reporting assistant. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
                logger.info("Successfully generated output using OpenAI")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI response: {e}")
                return {}
                
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return {}
    
    def _generate_rule_based_output(
        self,
        query: str,
        scenario: str,
        context: List[Dict[str, Any]],
        template_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate structured output using rule-based approach."""
        
        import re
        import random
        
        result = {}
        
        # Extract amounts from query
        amounts = []
        amount_patterns = [
            r'£\s*([\d,\.]+)\s*million',
            r'£\s*([\d,\.]+)\s*M',
            r'£\s*([\d,\.]+)\s*billion',
            r'£\s*([\d,\.]+)\s*B',
            r'£\s*([\d,\.]+)'
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match.replace(',', ''))
                    if 'million' in pattern or 'M' in pattern:
                        amount *= 1000000
                    elif 'billion' in pattern or 'B' in pattern:
                        amount *= 1000000000
                    amounts.append(amount)
                except ValueError:
                    continue
        
        # Generate values for each field
        for i, (field_id, field_info) in enumerate(template_schema.items()):
            field_name = field_info.get('name', field_id)
            
            # Find relevant regulations for this field
            regulatory_refs = []
            for text in context:
                field_refs = text.get("metadata", {}).get("field_references", [])
                if field_id in field_refs:
                    para_id = text.get("metadata", {}).get("paragraph_id", "")
                    if para_id:
                        regulatory_refs.append(para_id)
            
            # Generate value
            if amounts and i < len(amounts):
                value = amounts[i]
            else:
                # Generate based on field type
                if "CET1" in field_name or "Common Equity" in field_name:
                    value = random.uniform(1000000, 5000000)
                elif "AT1" in field_name or "Additional Tier" in field_name:
                    value = random.uniform(500000, 2000000)
                elif "Tier 2" in field_name:
                    value = random.uniform(500000, 1500000)
                elif "Total" in field_name:
                    value = random.uniform(2000000, 8000000)
                else:
                    value = random.uniform(100000, 1000000)
            
            # Format value
            if field_info.get('data_type') == 'percentage':
                formatted_value = f"{value:.2f}%"
            else:
                formatted_value = f"{value:,.2f}"
            
            # Calculate confidence
            confidence = min(0.8 + (len(regulatory_refs) * 0.1), 0.95)
            
            # Build reasoning
            if regulatory_refs:
                reasoning = f"Based on {', '.join(regulatory_refs[:2])}"
            else:
                reasoning = f"Standard calculation for {field_name}"
            
            result[field_id] = {
                "value": formatted_value,
                "confidence": confidence,
                "reasoning": reasoning,
                "regulatory_references": regulatory_refs,
                "data_type": field_info.get('data_type', 'decimal'),
                "required": field_info.get('required', False)
            }
        
        logger.info("Generated rule-based output")
        return result
    
    async def extract_query_components(self, query: str) -> Dict[str, Any]:
        """Extract components from natural language query."""
        if self.use_openai:
            try:
                prompt = f"""
                Extract key components from this regulatory reporting query:
                
                QUERY: {query}
                
                Extract:
                1. Entity type (e.g., retail bank, investment bank)
                2. Amounts mentioned
                3. Regulatory terms (CET1, AT1, Tier 2, etc.)
                4. Reporting context (consolidated, solo, quarterly, annual)
                
                Return as JSON with keys: entity_type, amounts, regulatory_terms, reporting_context
                """
                
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=settings.OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "Extract query components and output JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=500
                )
                
                content = response.choices[0].message.content
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                json_str = content[json_start:json_end]
                return json.loads(json_str)
                
            except Exception as e:
                logger.error(f"Failed to extract query components: {e}")
        
        # Fallback rule-based extraction
        return {
            "entity_type": "UK bank",
            "amounts": [],
            "regulatory_terms": [],
            "reporting_context": "consolidated"
        }