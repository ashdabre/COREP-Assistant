import streamlit as st

# st.title("AShalt Page")
# st.write("If you see this, Streamlit is working!")
# st.button("Click me")

import requests
import json

st.set_page_config(
    page_title="COREP Assistant",
    layout="wide"
)

st.title("🏦 COREP Regulatory Reporting Assistant")
st.markdown("LLM-assisted PRA COREP reporting assistant prototype")

# Initialize session state
if 'result' not in st.session_state:
    st.session_state.result = None

# Sidebar
with st.sidebar:
    st.header("Configuration")
    api_url = st.text_input("API URL", "http://localhost:8000")
    
    # Check API
    if st.button("Check API Status"):
        try:
            response = requests.get(f"{api_url}/")
            if response.status_code == 200:
                st.success("✅ API is running")
                st.json(response.json())
            else:
                st.error(f"❌ API error: {response.status_code}")
        except:
            st.error("❌ Cannot connect to API")
    
    st.divider()
    
    # Template selection
    template = st.selectbox(
        "COREP Template",
        ["C_01.00 - Own Funds", "C_02.00 - Capital Requirements"]
    )
    template_id = template.split(" - ")[0]

# Main content
st.header("📝 Input Query")

question = st.text_area(
    "Enter your regulatory question:",
    placeholder="e.g., What is Common Equity Tier 1 capital for a bank with £2M in qualifying instruments?",
    height=100
)

scenario = st.text_area(
    "Additional scenario (optional):",
    placeholder="e.g., UK retail bank, standardised approach...",
    height=80
)

if st.button("Generate Report", type="primary"):
    if not question:
        st.error("Please enter a question")
    else:
        with st.spinner("Processing your query..."):
            try:
                payload = {
                    "question": question,
                    "scenario": scenario,
                    "template_id": template_id
                }
                
                response = requests.post(
                    f"{api_url}/api/v1/report",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    st.session_state.result = response.json()
                    st.success("✅ Report generated!")
                else:
                    st.error(f"API Error: {response.status_code}")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API. Is the backend running?")
                st.info("Start backend with: `uvicorn src.main:app --reload`")
                
                # Show mock data for demo
                st.session_state.result = {
                    "session_id": "demo-123",
                    "template_id": template_id,
                    "populated_fields": {
                        "C_01.00_r010_c010": {
                            "value": "1500000.00",
                            "confidence": 0.95,
                            "reasoning": "Based on sample regulatory text"
                        }
                    },
                    "message": "Mock data - API not connected"
                }
                st.warning("Showing mock data for demonstration")

# Display results
if st.session_state.result:
    result = st.session_state.result
    
    st.header("📊 Results")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Template", "Validation", "Raw Data"])
    
    with tab1:
        st.subheader("Populated Fields")
        if "populated_fields" in result:
            for field_id, field_data in result["populated_fields"].items():
                with st.expander(f"Field: {field_id}"):
                    if isinstance(field_data, dict):
                        st.write(f"**Value**: {field_data.get('value', 'N/A')}")
                        st.write(f"**Confidence**: {field_data.get('confidence', 'N/A')}")
                        if field_data.get('reasoning'):
                            st.write(f"**Reasoning**: {field_data.get('reasoning')}")
                    else:
                        st.write(f"**Value**: {field_data}")
    
    with tab2:
        st.subheader("Validation Results")
        if "validation_results" in result:
            validation = result["validation_results"]
            if validation.get("valid", False):
                st.success("✅ All validations passed")
            else:
                st.error("❌ Validation errors found")
                for error in validation.get("errors", []):
                    st.error(f"{error.get('field', 'Unknown')}: {error.get('message', 'Unknown error')}")
    
    with tab3:
        st.subheader("Raw Response")
        st.json(result)

# Footer
st.divider()
st.caption("COREP Regulatory Assistant Prototype - End-to-End Demonstration")