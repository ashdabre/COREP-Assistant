import streamlit as st
import requests
import json
import time
import pandas as pd
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="COREP Regulatory Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'report_result' not in st.session_state:
    st.session_state.report_result = None
if 'processing_steps' not in st.session_state:
    st.session_state.processing_steps = []
if 'api_url' not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
if 'vector_db_stats' not in st.session_state:
    st.session_state.vector_db_stats = None
if 'system_info' not in st.session_state:
    st.session_state.system_info = None

# Custom CSS with enhanced styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #E5E7EB;
    }
    .workflow-step {
        background: white;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #3B82F6;
        transition: transform 0.3s;
    }
    .workflow-step:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .field-card {
        background: #F9FAFB;
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
        border: 1px solid #E5E7EB;
        transition: all 0.3s;
    }
    .field-card:hover {
        background: #F3F4F6;
        border-color: #3B82F6;
    }
    .audit-trail {
        background: #FEFCE8;
        border-left: 4px solid #F59E0B;
        padding: 15px;
        margin: 10px 0;
        border-radius: 0 8px 8px 0;
    }
    .validation-pass {
        background: #D1FAE5;
        color: #065F46;
        padding: 10px;
        border-radius: 6px;
        margin: 5px 0;
    }
    .validation-fail {
        background: #FEE2E2;
        color: #991B1B;
        padding: 10px;
        border-radius: 6px;
        margin: 5px 0;
    }
    .validation-warning {
        background: #FEF3C7;
        color: #92400E;
        padding: 10px;
        border-radius: 6px;
        margin: 5px 0;
    }
    .confidence-high { 
        color: #10B981; 
        font-weight: 700;
        background: #D1FAE5;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.9em;
    }
    .confidence-medium { 
        color: #F59E0B; 
        font-weight: 700;
        background: #FEF3C7;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.9em;
    }
    .confidence-low { 
        color: #EF4444; 
        font-weight: 700;
        background: #FEE2E2;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.9em;
    }
    .template-header {
        background: linear-gradient(90deg, #1E3A8A, #3B82F6);
        color: white;
        padding: 15px;
        border-radius: 10px 10px 0 0;
        margin-bottom: 0;
    }
    .database-info {
        background: #F0F9FF;
        border: 1px solid #E0F2FE;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    .rule-badge {
        background: #EDE9FE;
        color: #5B21B6;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        display: inline-block;
        margin: 2px;
    }
</style>
""", unsafe_allow_html=True)

def check_api_health(api_url):
    """Check if the API is running and get system info."""
    try:
        # Check basic API
        response = requests.get(f"{api_url}/", timeout=5)
        
        # Get system info
        try:
            stats_response = requests.get(f"{api_url}/api/v1/system-info", timeout=5)
            if stats_response.status_code == 200:
                st.session_state.system_info = stats_response.json()
        except:
            st.session_state.system_info = None
        
        # Get vector stats
        try:
            vector_response = requests.get(f"{api_url}/api/v1/vector-stats", timeout=5)
            if vector_response.status_code == 200:
                st.session_state.vector_db_stats = vector_response.json()
        except:
            st.session_state.vector_db_stats = None
        
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def get_confidence_class(confidence):
    """Get CSS class for confidence score."""
    if isinstance(confidence, str):
        try:
            confidence = float(confidence)
        except:
            return "confidence-low"
    
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.5:
        return "confidence-medium"
    else:
        return "confidence-low"

def display_database_info():
    """Display database information."""
    if st.session_state.system_info:
        info = st.session_state.system_info
        
        with st.expander("📊 System & Database Information", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("System", info["system"]["name"])
                st.caption(f"Version: {info['system']['version']}")
            
            with col2:
                if "sql" in info["databases"] and info["databases"]["sql"]["status"] == "connected":
                    st.metric("SQL Database", f"{info['databases']['sql']['regulatory_texts_count']} texts")
                else:
                    st.error("SQL Database: Offline")
            
            with col3:
                if "vector" in info["databases"] and info["databases"]["vector"]["status"] == "connected":
                    st.metric("Vector Database", f"{info['databases']['vector']['document_count']} docs")
                else:
                    st.error("Vector DB: Offline")
            
            # Database details
            st.markdown("##### Database Details")
            
            if "sql" in info["databases"]:
                sql_info = info["databases"]["sql"]
                if sql_info["status"] == "connected":
                    st.markdown(f"""
                    **SQLite Database:**
                    - Location: `{sql_info['path']}`
                    - Tables: {', '.join(sql_info['tables'])}
                    - Regulatory Texts: {sql_info['regulatory_texts_count']}
                    """)
            
            if "vector" in info["databases"]:
                vector_info = info["databases"]["vector"]
                if vector_info["status"] == "connected":
                    st.markdown(f"""
                    **Vector Database (ChromaDB):**
                    - Location: `{vector_info['path']}`
                    - Collection: {vector_info['collection']}
                    - Documents: {vector_info['document_count']}
                    - Model: {vector_info['embedding_model']}
                    """)
            
            # Data files
            if info["data_files"]:
                st.markdown("##### Data Files")
                for file_path, file_info in info["data_files"].items():
                    if file_info.get("exists"):
                        st.success(f"✅ {file_path}: {file_info.get('rule_count', '?')} rules")
                    else:
                        st.error(f"❌ {file_path}: Missing")

def display_workflow_steps():
    """Display the complete workflow steps."""
    st.markdown("### 🔄 End-to-End Workflow")
    
    workflow_data = [
        {"step": 1, "title": "Natural Language Query", "icon": "💬", "description": "Analyst asks question in plain English"},
        {"step": 2, "title": "Regulatory Retrieval", "icon": "🔍", "description": "Relevant PRA Rulebook sections retrieved from vector DB"},
        {"step": 3, "title": "Rule Processing", "icon": "⚖️", "description": "Rules processed and mapped to COREP fields"},
        {"step": 4, "title": "Template Population", "icon": "📋", "description": "Fields populated with values and confidence scores"},
        {"step": 5, "title": "Validation & Audit", "icon": "✅", "description": "Data validated, audit trail generated"},
        {"step": 6, "title": "Report Generation", "icon": "📊", "description": "Complete report with regulatory references"}
    ]
    
    cols = st.columns(3)
    for idx, step in enumerate(workflow_data):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="workflow-step">
                <div style="font-size: 1.5rem; margin-bottom: 10px;">{step['icon']} <strong>Step {step['step']}</strong></div>
                <div style="font-weight: 600; color: #1E3A8A; margin-bottom: 5px;">{step['title']}</div>
                <div style="font-size: 0.9rem; color: #6B7280;">{step['description']}</div>
            </div>
            """, unsafe_allow_html=True)

def display_validation_details(validation_results, template_id):
    """Display detailed validation results."""
    from src.config.corep_templates import COREP_TEMPLATES
    
    template = COREP_TEMPLATES.get(template_id, {})
    
    # Field-level validations
    if hasattr(validation_results, 'dict'):
        validation_results = validation_results.dict()
    
    st.markdown("##### 📋 Field-Level Validation Rules Applied")
    
    # Get template validation rules
    template_fields = template.get("fields", {})
    
    validation_table_data = []
    
    for field_id, field_info in template_fields.items():
        validation_rules = field_info.get("validation", [])
        
        for rule in validation_rules:
            # Check if this rule was violated
            violated = False
            error_message = ""
            
            if "errors" in validation_results:
                for error in validation_results["errors"]:
                    if error.get("field") == field_id:
                        violated = True
                        error_message = error.get("message", "")
                        break
            
            if not violated and "warnings" in validation_results:
                for warning in validation_results["warnings"]:
                    if warning.get("field") == field_id:
                        violated = True  # Treat warnings as violations for display
                        error_message = warning.get("message", "")
                        break
            
            rule_name = rule.replace("_", " ").title()
            
            if "range:" in rule:
                range_val = rule.replace("range:", "")
                rule_name = f"Range: {range_val}"
            elif "decimal_places:" in rule:
                places = rule.split(":")[1]
                rule_name = f"Decimal Places: {places}"
            elif "equals_sum:" in rule:
                formula = rule.replace("equals_sum:", "")
                rule_name = f"Equals Sum: {formula}"
            
            validation_table_data.append({
                "Field": field_id,
                "Field Name": field_info.get("name", field_id),
                "Validation Rule": rule_name,
                "Status": "❌ FAILED" if violated else "✅ PASSED",
                "Message": error_message if violated else "Rule satisfied"
            })
    
    if validation_table_data:
        df = pd.DataFrame(validation_table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No field-level validation rules defined for this template")
    
    # Regulatory validation rules
    st.markdown("##### ⚖️ Regulatory Validation Rules Applied")
    
    if st.session_state.report_result and "relevant_regulations" in st.session_state.report_result:
        regulatory_rules = []
        
        for reg in st.session_state.report_result["relevant_regulations"]:
            metadata = reg.get("metadata", {})
            rules = metadata.get("validation_rules", [])
            para_id = metadata.get("paragraph_id", "")
            
            if rules:
                for rule in rules:
                    # Check if violated
                    violated = False
                    message = ""
                    
                    if "rule_violations" in validation_results:
                        for violation in validation_results["rule_violations"]:
                            if violation.get("rule_id") == para_id:
                                violated = True
                                message = violation.get("message", "")
                                break
                    
                    rule_display = rule
                    if "range:" in rule:
                        range_val = rule.replace("range:", "")
                        rule_display = f"Range {range_val}"
                    elif "equals_sum:" in rule:
                        formula = rule.replace("equals_sum:", "")
                        rule_display = f"Sum equals {formula}"
                    
                    regulatory_rules.append({
                        "Regulation": para_id,
                        "Validation Rule": rule_display,
                        "Status": "❌ VIOLATED" if violated else "✅ APPLIED",
                        "Message": message if violated else "Compliant",
                        "Fields": ", ".join(metadata.get("field_references", []))
                    })
        
        if regulatory_rules:
            df_reg = pd.DataFrame(regulatory_rules)
            st.dataframe(df_reg, use_container_width=True, hide_index=True)
        else:
            st.info("No regulatory validation rules found in retrieved regulations")
    
    # Template validation rules
    st.markdown("##### 🧩 Template-Level Validation Rules")
    
    template_rules = template.get("validation_rules", [])
    if template_rules:
        template_validation_data = []
        
        for rule in template_rules:
            # Check if violated
            violated = False
            message = ""
            
            if "errors" in validation_results:
                for error in validation_results["errors"]:
                    if error.get("rule_id") == rule.get("rule_id"):
                        violated = True
                        message = error.get("message", "")
                        break
            
            template_validation_data.append({
                "Rule ID": rule.get("rule_id", ""),
                "Description": rule.get("description", ""),
                "Severity": rule.get("severity", "error").upper(),
                "Status": "❌ FAILED" if violated else "✅ PASSED",
                "Message": message if violated else "Rule satisfied"
            })
        
        df_template = pd.DataFrame(template_validation_data)
        st.dataframe(df_template, use_container_width=True, hide_index=True)
    else:
        st.info("No template-level validation rules defined")

def main():
    # Header with gradient title
    st.markdown('<div class="main-title">🏦 LLM-assisted PRA COREP Reporting Assistant</div>', unsafe_allow_html=True)
    
    st.markdown("""
    **UK Banks subject to the PRA Rulebook** must submit COREP regulatory returns that accurately reflect their capital, 
    risk exposures and other prudential metrics. This prototype demonstrates **end-to-end behaviour** from user question → 
    retrieval of regulatory text → structured LLM output → populated template extract.
    """)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="template-header">⚙️ Configuration</div>', unsafe_allow_html=True)
        
        # API Configuration
        api_url = st.text_input("**API URL**", "http://localhost:8000")
        st.session_state.api_url = api_url
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Check System Status", type="secondary", use_container_width=True):
                with st.spinner("Checking..."):
                    is_healthy, health_data = check_api_health(api_url)
                    if is_healthy:
                        st.success("✅ System Running")
                    else:
                        st.error("❌ System Offline")
        
        with col2:
            if st.button("View API Docs", type="secondary", use_container_width=True):
                st.markdown(f"[Open API Documentation]({api_url}/api/docs)", unsafe_allow_html=True)
        
        st.divider()
        
        # Template Selection
        st.markdown("### 📋 COREP Template")
        template_option = st.selectbox(
            "Select Template",
            [
                "C_01.00 - Own Funds (Capital)",
                "C_02.00 - Capital Requirements",
            ]
        )
        
        template_id = template_option.split(" - ")[0]
        template_name = template_option.split(" - ")[1]
        
        # Show template info
        with st.expander("Template Details", expanded=True):
            from src.config.corep_templates import COREP_TEMPLATES
            template = COREP_TEMPLATES.get(template_id, {})
            
            st.markdown(f"**{template.get('name', '')}**")
            st.caption(template.get('description', ''))
            
            st.markdown("**Fields:**")
            fields = template.get("fields", {})
            for field_id, field_info in fields.items():
                required = "✅" if field_info.get("required") else "➖"
                st.markdown(f"- {required} `{field_id}`: {field_info.get('name', '')}")
        
        st.divider()
        
        # Database Information
        display_database_info()
        
        st.divider()
        
        # Sample Queries
        st.markdown("### 💡 Sample Queries")
        sample_queries = [
            "What is Common Equity Tier 1 capital for a bank with £2 million in qualifying instruments and £750,000 retained earnings?",
            "Calculate Additional Tier 1 capital for a UK retail bank with £1.5M CET1 instruments",
            "What are the minimum capital ratio requirements under CRD V?",
            "How to calculate Tier 2 capital for standardised approach banks?"
        ]
        
        for query in sample_queries:
            if st.button(f"📝 {query[:40]}...", use_container_width=True, key=f"sample_{hash(query)}"):
                st.session_state.question = query
                st.rerun()
        
        st.divider()
        
        # Reset button
        if st.button("🔄 Reset All", type="secondary", use_container_width=True):
            st.session_state.report_result = None
            st.session_state.processing_steps = []
            st.rerun()
    
    # Main content - Two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 📝 Input: Natural Language Query")
        
        # Query input
        question = st.text_area(
            "**Regulatory Question:**",
            value=st.session_state.get("question", ""),
            placeholder="e.g., What should be reported as Common Equity Tier 1 capital for a bank with £1.5 million in qualifying capital instruments and £500,000 retained earnings?",
            height=120,
            help="Ask a natural language question about COREP reporting"
        )
        
        # Scenario input
        scenario = st.text_area(
            "**Reporting Scenario (Optional):**",
            placeholder="e.g., UK retail bank, standardised approach for credit risk, consolidated basis, reporting as of Q4 2023...",
            height=80,
            help="Provide additional context about the reporting scenario"
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            col_a, col_b = st.columns(2)
            with col_a:
                retrieval_count = st.slider("Rules to retrieve", 1, 10, 3)
            with col_b:
                confidence_threshold = st.slider("Confidence threshold", 0.0, 1.0, 0.6, 0.1)
        
        # Generate Report button
        if st.button("🚀 Generate COREP Report", type="primary", use_container_width=True):
            if not question:
                st.error("Please enter a regulatory question")
            else:
                # Clear previous results
                st.session_state.report_result = None
                st.session_state.processing_steps = []
                
                # Create progress container
                progress_container = st.container()
                with progress_container:
                    # Show processing steps
                    steps = [
                        ("Parsing natural language query...", 10),
                        ("Querying vector database for regulatory rules...", 25),
                        (f"Retrieving top {retrieval_count} relevant rules...", 40),
                        ("Processing rules and mapping to COREP fields...", 60),
                        ("Calculating field values and confidence scores...", 75),
                        ("Validating data against regulatory requirements...", 85),
                        ("Generating audit trail and final report...", 95),
                        ("Complete!", 100)
                    ]
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for step_name, progress in steps:
                        status_text.text(f"⏳ {step_name}")
                        time.sleep(0.4)
                        progress_bar.progress(progress)
                        st.session_state.processing_steps.append({
                            "name": step_name,
                            "progress": progress,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                    
                    # Make API call
                    try:
                        payload = {
                            "question": question,
                            "scenario": scenario,
                            "template_id": template_id,
                            "retrieval_count": retrieval_count,
                            "confidence_threshold": confidence_threshold
                        }
                        
                        response = requests.post(
                            f"{api_url}/api/v1/report",
                            json=payload,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.report_result = result
                            status_text.success("✅ Report generated successfully!")
                            time.sleep(0.5)
                            progress_bar.empty()
                            status_text.empty()
                            st.rerun()
                        else:
                            st.error(f"API Error {response.status_code}: {response.text}")
                            status_text.error("❌ Report generation failed")
                            
                    except requests.exceptions.ConnectionError:
                        st.error(f"❌ Cannot connect to API at {api_url}")
                        st.info("Make sure backend is running: `uvicorn src.main:app --reload`")
                        
                        # Show enhanced mock data
                        st.session_state.report_result = generate_enhanced_mock_response(
                            question, scenario, template_id, retrieval_count
                        )
                        st.warning("⚠️ Showing enhanced mock data (API unavailable)")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
    
    with col2:
        st.markdown("### 📊 Processing & Results")
        
        if st.session_state.processing_steps:
            with st.expander("📋 Processing Timeline", expanded=True):
                for step in st.session_state.processing_steps:
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.text(step["name"])
                    with col_b:
                        st.text(f"{step['progress']}%")
        
        if st.session_state.report_result:
            result = st.session_state.report_result
            
            # Success banner
            st.success(f"""
            ✅ **Report Generated Successfully!**  
            **Session ID:** {result.get('session_id', 'N/A')}  
            **Template:** {result.get('template_id', 'N/A')}  
            **Processing Time:** {result.get('processing_time_ms', 0)}ms  
            **Overall Confidence:** {result.get('confidence_score', 0):.1%}
            """)
            
            # Tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📋 Template", "✅ Validation", "📚 Audit Trail", "⚖️ Regulations", "📄 Raw Data"
            ])
            
            with tab1:
                st.markdown("#### Populated Template Fields")
                
                if "populated_fields" in result and result["populated_fields"]:
                    for field_id, field_data in result["populated_fields"].items():
                        with st.expander(f"**{field_id}**", expanded=True):
                            if isinstance(field_data, dict):
                                # Display field info
                                col1, col2, col3 = st.columns([2, 1, 1])
                                with col1:
                                    st.metric("Value", field_data.get('value', 'N/A'))
                                with col2:
                                    confidence = field_data.get('confidence', 0)
                                    confidence_class = get_confidence_class(confidence)
                                    st.markdown(f"<div class='{confidence_class}'>{confidence:.1%}</div>", unsafe_allow_html=True)
                                with col3:
                                    if field_data.get('required'):
                                        st.info("Required")
                                
                                # Display reasoning
                                if field_data.get('reasoning'):
                                    st.markdown("**Reasoning:**")
                                    st.info(field_data.get('reasoning'))
                                
                                # Display regulatory references
                                if field_data.get('regulatory_references'):
                                    st.markdown("**Regulatory References:**")
                                    for ref in field_data.get('regulatory_references', []):
                                        st.markdown(f"- `{ref}`")
                                
                                # Display validation rules
                                from src.config.corep_templates import COREP_TEMPLATES
                                template = COREP_TEMPLATES.get(template_id, {})
                                field_info = template.get("fields", {}).get(field_id, {})
                                validation_rules = field_info.get("validation", [])
                                
                                if validation_rules:
                                    st.markdown("**Validation Rules:**")
                                    for rule in validation_rules:
                                        st.markdown(f"<span class='rule-badge'>{rule}</span>", unsafe_allow_html=True)
                else:
                    st.info("No fields populated")
            
            with tab2:
                st.markdown("#### Validation Results")
                
                if "validation_results" in result:
                    validation = result["validation_results"]
                    
                    # Summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if validation.get("valid", False):
                            st.success("✅ **VALID**")
                        else:
                            st.error("❌ **INVALID**")
                    with col2:
                        st.metric("Checks", validation.get("checks_performed", 0))
                    with col3:
                        errors = len(validation.get("errors", []))
                        warnings = len(validation.get("warnings", []))
                        st.metric("Issues", f"{errors}E/{warnings}W")
                    
                    # Show detailed validation
                    display_validation_details(validation, template_id)
                    
                    # Show errors
                    if validation.get("errors"):
                        st.markdown("##### ❌ Errors")
                        for error in validation.get("errors", []):
                            st.error(f"**{error.get('field', 'Unknown')}**: {error.get('message', 'Unknown')}")
                    
                    # Show warnings
                    if validation.get("warnings"):
                        st.markdown("##### ⚠️ Warnings")
                        for warning in validation.get("warnings", []):
                            st.warning(f"**{warning.get('field', 'Unknown')}**: {warning.get('message', 'Unknown')}")
            
            with tab3:
                st.markdown("#### 📚 Audit Trail")
                
                if "audit_trail" in result and result["audit_trail"]:
                    st.markdown("""
                    <div class="audit-trail">
                        <strong>Audit Log:</strong> This shows which regulatory paragraphs were used to justify each populated field.
                        Each field is mapped to specific PRA Rulebook sections.
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for field_id, refs in result["audit_trail"].items():
                        if refs:
                            with st.expander(f"**{field_id}** → {len(refs)} regulatory reference(s)"):
                                for ref in refs:
                                    # Find the regulation content
                                    regulation_content = ""
                                    for reg in result.get("relevant_regulations", []):
                                        if reg.get("metadata", {}).get("paragraph_id") == ref:
                                            regulation_content = reg.get("content", "")[:200] + "..."
                                            break
                                    
                                    st.markdown(f"**`{ref}`**")
                                    st.caption(regulation_content)
                else:
                    st.info("No audit trail available")
            
            with tab4:
                st.markdown("#### ⚖️ Retrieved Regulations")
                
                if "relevant_regulations" in result and result["relevant_regulations"]:
                    st.info(f"**Retrieved {len(result['relevant_regulations'])} relevant regulatory rules**")
                    
                    for i, regulation in enumerate(result["relevant_regulations"], 1):
                        metadata = regulation.get("metadata", {})
                        with st.expander(f"{i}. {metadata.get('paragraph_id', 'Rule')} (Score: {regulation.get('similarity_score', 0):.3f})"):
                            st.markdown(f"**Source:** {metadata.get('source', 'Unknown')}")
                            st.markdown(f"**Section:** {metadata.get('section', 'Unknown')}")
                            st.markdown(f"**Template Reference:** {metadata.get('template_reference', 'N/A')}")
                            
                            # Show field mappings
                            field_refs = metadata.get('field_references', [])
                            if field_refs:
                                st.markdown("**Maps to fields:**")
                                for field_ref in field_refs:
                                    st.markdown(f"- `{field_ref}`")
                            
                            # Show validation rules
                            validation_rules = metadata.get('validation_rules', [])
                            if validation_rules:
                                st.markdown("**Validation Rules:**")
                                for rule in validation_rules:
                                    st.markdown(f"<span class='rule-badge'>{rule}</span>", unsafe_allow_html=True)
                            
                            # Show content
                            st.markdown("**Content:**")
                            st.write(regulation.get("content", ""))
                else:
                    st.info("No regulations retrieved")
            
            with tab5:
                st.markdown("#### 📄 Raw API Response")
                st.json(result)
        
        else:
            # Display workflow when no results
            display_workflow_steps()
            
            # Show placeholder
            st.markdown("""
            <div style="background: #F9FAFB; border-radius: 10px; padding: 40px; text-align: center; margin-top: 20px;">
                <div style="font-size: 4rem; margin-bottom: 20px;">📊</div>
                <h3 style="color: #6B7280;">Report Output Will Appear Here</h3>
                <p style="color: #9CA3AF;">Submit a query to see the complete end-to-end workflow:</p>
                <ol style="text-align: left; display: inline-block; color: #6B7280;">
                    <li>Natural language query processing</li>
                    <li>Regulatory text retrieval from vector database</li>
                    <li>Rule mapping to COREP fields</li>
                    <li>Template population with validation</li>
                    <li>Audit trail generation</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer with system info
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption(f"**Backend API:** {api_url}")
    with col2:
        if st.session_state.vector_db_stats:
            count = st.session_state.vector_db_stats.get('document_count', 0)
            st.caption(f"**Vector DB:** {count} rules loaded")
    with col3:
        st.caption(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def generate_enhanced_mock_response(question, scenario, template_id, retrieval_count=3):
    """Generate enhanced mock response with realistic regulatory data."""
    import re
    import time
    import random
    
    # Extract amounts
    amounts = []
    for pattern in [r'£\s*([\d,\.]+)\s*million', r'£\s*([\d,\.]+)']:
        matches = re.findall(pattern, question, re.IGNORECASE)
        for match in matches:
            try:
                amount = float(match.replace(',', ''))
                if 'million' in pattern.lower():
                    amount *= 1000000
                amounts.append(amount)
            except:
                pass
    
    if not amounts:
        amounts = [1500000.00, 500000.00, 750000.00, 2750000.00]
    
    # Generate populated fields based on template
    populated_fields = {}
    
    if template_id == "C_01.00":
        field_configs = [
            ("C_01.00_r010_c010", "Common Equity Tier 1 capital", 1500000, ["PRA_RB_4.2.1"]),
            ("C_01.00_r020_c010", "Additional Tier 1 capital", 500000, ["PRA_RB_4.2.5"]),
            ("C_01.00_r030_c010", "Tier 2 capital", 750000, ["PRA_RB_4.2.8"]),
            ("C_01.00_r040_c010", "Total eligible capital", 2750000, ["PRA_RB_4.2.12"])
        ]
    else:
        field_configs = [
            ("C_02.00_r010_c010", "Minimum CET1 ratio", 4.5, ["PRA_RB_4.3.1"]),
            ("C_02.00_r020_c010", "Minimum Tier 1 ratio", 6.0, ["PRA_RB_4.3.1"]),
            ("C_02.00_r030_c010", "Minimum Total capital ratio", 8.0, ["PRA_RB_4.3.1"]),
            ("C_02.00_r040_c010", "Capital conservation buffer", 2.5, ["PRA_RB_4.3.5"])
        ]
    
    for i, (field_id, field_name, default_value, refs) in enumerate(field_configs):
        if i < len(amounts):
            value = amounts[i]
        else:
            value = default_value
        
        # Add some randomness
        value = value * random.uniform(0.9, 1.1)
        
        if "ratio" in field_name.lower() or "buffer" in field_name.lower():
            formatted_value = f"{value:.2f}%"
        else:
            formatted_value = f"{value:,.2f}"
        
        populated_fields[field_id] = {
            "value": formatted_value,
            "confidence": random.uniform(0.7, 0.95),
            "reasoning": f"Based on {', '.join(refs)}: {field_name} calculation",
            "regulatory_references": refs,
            "data_type": "percentage" if "%" in formatted_value else "decimal",
            "required": True,
            "field_name": field_name
        }
    
    # Mock regulatory texts
    relevant_regulations = [
        {
            "content": "Common Equity Tier 1 (CET1) capital shall consist of the sum of the following elements...",
            "metadata": {
                "paragraph_id": "PRA_RB_4.2.1",
                "source": "PRA Rulebook",
                "section": "Own Funds",
                "template_reference": "C_01.00",
                "field_references": ["C_01.00_r010_c010"],
                "effective_date": "2023-01-01",
                "validation_rules": ["positive_decimal", "required"]
            },
            "similarity_score": 0.92
        },
        {
            "content": "Additional Tier 1 (AT1) capital shall consist of capital instruments that meet the criteria...",
            "metadata": {
                "paragraph_id": "PRA_RB_4.2.5",
                "source": "PRA Rulebook",
                "section": "Own Funds",
                "template_reference": "C_01.00",
                "field_references": ["C_01.00_r020_c010"],
                "effective_date": "2023-01-01",
                "validation_rules": ["positive_decimal", "required"]
            },
            "similarity_score": 0.88
        }
    ]
    
    # Mock validation results with detailed rules
    validation_results = {
        "valid": True,
        "errors": [],
        "warnings": [
            {
                "field": list(populated_fields.keys())[1],
                "message": "Confidence score below 90%",
                "severity": "warning",
                "rule_id": "WARN_001"
            }
        ],
        "checks_performed": len(populated_fields) * 3,
        "rule_violations": [],
        "field_validations": {
            field_id: [
                {"valid": True, "message": "Positive decimal validation passed", "rule_id": "POSITIVE_DECIMAL"},
                {"valid": True, "message": "Required field validation passed", "rule_id": "REQUIRED_FIELD"}
            ]
            for field_id in populated_fields.keys()
        }
    }
    
    # Create audit trail
    audit_trail = {
        field_id: populated_fields[field_id].get("regulatory_references", [])
        for field_id in populated_fields.keys()
    }
    
    return {
        "session_id": f"mock-{int(time.time())}",
        "template_id": template_id,
        "populated_fields": populated_fields,
        "template_output": {
            "template_id": template_id,
            "template_name": "Own Funds" if template_id == "C_01.00" else "Capital Requirements",
            "description": "COREP regulatory reporting template",
            "version": "1.0",
            "fields": [
                {
                    "field_id": field_id,
                    "field_name": data.get("field_name", field_id),
                    "value": data.get("value", ""),
                    "confidence": data.get("confidence", 0),
                    "data_type": data.get("data_type", "string"),
                    "required": data.get("required", False),
                    "regulatory_references": data.get("regulatory_references", []),
                    "reasoning": data.get("reasoning", "")
                }
                for field_id, data in populated_fields.items()
            ]
        },
        "audit_trail": audit_trail,
        "validation_results": validation_results,
        "relevant_regulations": relevant_regulations,
        "timestamp": datetime.now().isoformat(),
        "confidence_score": 0.85,
        "processing_time_ms": 2450,
        "message": "Enhanced mock response with detailed validation rules"
    }

if __name__ == "__main__":
    main()