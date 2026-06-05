import streamlit as st
from pypdf import PdfReader
import docx2txt
import json
from google import genai
from google.genai import types

st.set_page_config(page_title="Instant RFP Analyzer", page_icon="📋", layout="wide")

# 🔑 PASTE YOUR API KEY HERE ONCE AND FORGET IT:
# 🔑 Safe cloud-secured key mapping:
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
# Advanced helper function to extract text from multiple file types (PDF, DOCX, TXT)
def extract_text_from_multiple_files(uploaded_files):
    combined_text = ""
    for uploaded_file in uploaded_files:
        combined_text += f"\n--- START OF ATTACHMENT: {uploaded_file.name} ---\n"
        try:
            if uploaded_file.name.lower().endswith('.pdf'):
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        combined_text += text + "\n"
            elif uploaded_file.name.lower().endswith('.docx'):
                text = docx2txt.process(uploaded_file)
                if text:
                    combined_text += text + "\n"
            elif uploaded_file.name.lower().endswith('.txt'):
                text = uploaded_file.read().decode("utf-8")
                if text:
                    combined_text += text + "\n"
        except Exception as e:
            st.error(f"Error reading file {uploaded_file.name}: {e}")
        combined_text += f"\n--- END OF ATTACHMENT: {uploaded_file.name} ---\n"
    return combined_text

# --- UI Setup ---
st.title("📋 AI RFP Go/No-Go Evaluation Tool")
st.subheader("Just drop your files and run. No API keys required on-screen.")

# Layout Columns for Uploads
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🎯 Target RFP Documents")
    rfp_files = st.file_uploader(
        "Drop all RFP / requirement documents here", 
        type=["pdf", "docx", "txt"], 
        accept_multiple_files=True,
        key="rfp"
    )

with col2:
    st.markdown("### 🛡️ Your Company Assets")
    capability_files = st.file_uploader(
        "Drop all company profiles, case studies, or past bids here", 
        type=["pdf", "docx", "txt"], 
        accept_multiple_files=True,
        key="caps"
    )

# --- Processing & Analysis ---
if st.button("Run Go/No-Go Evaluation", type="primary"):
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE" or not GEMINI_API_KEY:
        st.error("Developer Error: Please open app.py and replace 'YOUR_GEMINI_API_KEY_HERE' with your real key.")
    elif not rfp_files or not capability_files:
        st.warning("Please upload files in both categories before running.")
    else:
        with st.spinner("Analyzing your documents... Please wait."):
            
            rfp_text = extract_text_from_multiple_files(rfp_files)
            caps_text = extract_text_from_multiple_files(capability_files)
            
            user_prompt = f"""
            You are an expert, conservative enterprise procurement officer. Your job is to analyze 
            the provided RFP documents against a company's internal capability attachments and issue a strict Go/No-Go recommendation. 
            Focus heavily on identifying hard gaps, missing qualifications, timeline risks, and strict penalties.
            
            [RFP DOCUMENTATION]
            {rfp_text}
            
            [OUR COMPANY CAPABILITIES]
            {caps_text}
            
            CRITICAL RULE: You must cite the specific filename and page/section references for every single point or gap you identify.
            
            Respond strictly in valid JSON format with this exact layout:
            {{
                "recommendation": "GO" or "NO-GO",
                "fit_score": 85,
                "executive_summary": "A brief 3-sentence summary of the decision.",
                "critical_gaps": ["Gap 1 with file/section citation", "Gap 2 with file/section citation"],
                "key_strengths": ["Strength 1", "Strength 2"],
                "hidden_risks": ["Risk details like strict SLAs, liquid damages, or short deadlines"]
            }}
            """
            
            try:
                # Uses the hidden hardcoded key automatically
                client = genai.Client(api_key=GEMINI_API_KEY)
                
                # Defaulting to gemini-2.5-flash for maximum speed and zero cost
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    ),
                )
                
                result = json.loads(response.text)
                
                # --- Render Results Dashboard ---
                st.success("Analysis Complete!")
                st.divider()
                
                m_col1, m_col2 = st.columns(2)
                with m_col1:
                    rec = result.get("recommendation", "NO-GO")
                    if rec == "GO":
                        st.markdown(f"## Decision: <span style='color:green'>{rec}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"## Decision: <span style='color:red'>{rec}</span>", unsafe_allow_html=True)
                        
                with m_col2:
                    st.metric(label="Overall Fit Score", value=f"{result.get('fit_score')}%")
                
                st.markdown(f"### 📝 Executive Summary\n{result.get('executive_summary')}")
                st.divider()
                
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.markdown("### 🛑 Critical Gaps & Mismatches")
                    for gap in result.get("critical_gaps", []):
                        st.error(gap)
                        
                    st.markdown("### ⚠️ Hidden Terms & Risks")
                    for risk in result.get("hidden_risks", []):
                        st.warning(risk)
                        
                with res_col2:
                    st.markdown("### 🛡️ Competitive Strengths")
                    for strength in result.get("key_strengths", []):
                        st.success(strength)
                        
            except Exception as e:
                st.error(f"An error occurred during API processing: {e}")