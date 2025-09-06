# claimbot_final_working.py
# 🛡️ AI Insurance Claims Assistant with Working TXT Download & Real Image-Text Verification
# Run with: streamlit run claimbot_final_working.py

import streamlit as st
import google.generativeai as genai
from PIL import Image
import base64
from datetime import datetime

# ————————————————————————————————
# 🔑 SET YOUR API KEY HERE
GEMINI_API_KEY = "AIzaSyDM3qZV71BD78ffMYi30_gCbjSSUbKy3KI"  # ← Replace with your regenerated key!
# ————————————————————————————————

# Configure Gemini
try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')  # Supports vision
except Exception as e:
    st.error("❌ Failed to configure Gemini API.")
    st.stop()

# ————————————————————————————————
# Sanitize Text (Avoid Encoding Issues)
# ————————————————————————————————
def sanitize_text(text):
    if not isinstance(text, str):
        text = str(text)
    replacements = {
        '\u2014': '-', '\u2013': '-', '\u201c': '"', '\u201d': '"',
        '\u2018': "'", '\u2019': "'", '\u2022': '*', '\u25cf': '*',
        '\u2026': '...', '\t': ' ', '\n': ' ', '\r': '', '  ': ' '
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode('ascii', errors='ignore').decode('ascii')

# ————————————————————————————————
# Streamlit UI
# ————————————————————————————————
st.markdown("<h1 style='text-align: center; color: #0066cc;'>🧠 AI Insurance Claims Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px;'>Upload <strong>before & after</strong> photos + description. AI verifies story vs. visuals.</p>", unsafe_allow_html=True)

# User inputs
user_text = st.text_input("📝 Describe what happened:", placeholder="e.g., My laptop was stolen from my desk...")

col1, col2 = st.columns(2)
with col1:
    uploaded_before = st.file_uploader("📷 Before Incident", type=["jpg", "jpeg", "png"], key="before")
with col2:
    uploaded_after = st.file_uploader("💥 After Incident", type=["jpg", "jpeg", "png"], key="after")

# ————————————————————————————————
# Submit Button
# ————————————————————————————————
if st.button("🚀 Analyze Claim", type="primary"):
    if not user_text:
        st.error("❌ Please enter a description of the incident.")
    elif not uploaded_before:
        st.warning("⚠️ Please upload a 'Before' photo for comparison.")
    elif not uploaded_after:
        st.warning("⚠️ Please upload an 'After' photo.")
    else:
        with st.spinner("🔍 Analyzing images and description with Gemini AI..."):

            try:
                # Open images
                before_img = Image.open(uploaded_before)
                after_img = Image.open(uploaded_after)

                # 🔥 CRITICAL: Use Gemini to analyze TEXT + BOTH IMAGES TOGETHER
                prompt = f"""
                You are an AI insurance analyst. Compare the 'Before' and 'After' images with the user's description.

                User says: "{user_text}"

                Analyze:
                1. What valuable items were visible in the 'Before' image?
                2. Which are missing or damaged in the 'After' image?
                3. Is the user's story consistent with the visual evidence?
                4. Is there any sign of fraud (e.g., claiming an item not in before photo)?

                Respond in JSON:
                {{
                  "claim_type": "theft/flood/fire/accident/vandalism",
                  "severity": "Low/Medium/High/Critical",
                  "items_before": ["list of items"],
                  "missing_items": ["items no longer present"],
                  "damaged_items": ["items visibly damaged"],
                  "visual_story_consistency": "High/Medium/Low",
                  "fraud_risk": "Low/Medium/High",
                  "reason_for_fraud_risk": "Brief explanation",
                  "recommendation": "Approve/Review Required/Reject"
                }}
                """

                # ✅ Pass both images AND text to Gemini
                response = model.generate_content([
                    prompt,
                    "Before Image:", before_img,
                    "After Image:", after_img
                ])

                # Parse response
                try:
                    text = response.text.strip()
                    if "```json" in text:
                        text = text.split("```json")[1].split("```")[0]
                    import json
                    analysis = json.loads(text)
                except Exception as e:
                    st.error("❌ Failed to parse AI response.")
                    st.code(response.text)
                    st.stop()

                # ————————————————————————————————
                # ✅ DISPLAY RESULTS IN BEAUTIFUL UI
                # ————————————————————————————————
                st.markdown("<h3 style='color:#003366;'>📋 Claim Summary</h3>", unsafe_allow_html=True)

                st.markdown(f"**Type:** `{sanitize_text(analysis.get('claim_type', 'N/A'))}`")
                st.markdown(f"**Severity:** `{sanitize_text(analysis.get('severity', 'N/A'))}`")

                # Fraud Risk
                fraud_risk = sanitize_text(analysis.get("fraud_risk", "Low"))
                if fraud_risk.lower() == "high":
                    st.markdown(f"<p style='background-color:#fff3cd; color:#856404; padding:10px; border-radius:5px; text-align:center; font-weight:bold;'>⚠️ High Fraud Risk: {sanitize_text(analysis.get('reason_for_fraud_risk', ''))}</p>", unsafe_allow_html=True)
                else:
                    st.markdown(f"**Fraud Risk:** `{fraud_risk}`")

                # Items
                st.markdown("<h3 style='color:#003366;'>📦 Item Analysis</h3>", unsafe_allow_html=True)

                def show_items(items, color="#333"):
                    if isinstance(items, list) and items:
                        items = [sanitize_text(i) for i in items]
                        st.markdown(f"<p style='color:{color}; font-size:15px;'>{' • '.join([f'`{i}`' for i in items])}</p>", unsafe_allow_html=True)
                    else:
                        st.markdown("<p style='color:#888; font-size:15px;'>None detected</p>", unsafe_allow_html=True)

                st.write("**Items Before:**")
                show_items(analysis.get("items_before"))

                st.write("**Missing Items:**")
                show_items(analysis.get("missing_items"), "#d7003a")

                st.write("**Damaged Items:**")
                show_items(analysis.get("damaged_items"), "#b35a00")

                # Consistency
                st.markdown("<h3 style='color:#003366;'>🔍 Story vs. Visuals</h3>", unsafe_allow_html=True)
                consistency = sanitize_text(analysis.get("visual_story_consistency", "N/A"))
                st.markdown(f"**Consistency:** `{consistency}`")
                st.markdown(f"**AI Reasoning:** *{sanitize_text(analysis.get('reason_for_fraud_risk', 'No issues detected.'))}*")

                # Recommendation
                st.markdown("<h3 style='color:#003366;'>💡 Recommendation</h3>", unsafe_allow_html=True)
                st.markdown(f"<p style='background-color:#e7f3ff; padding:15px; border-radius:5px;'><strong>{sanitize_text(analysis.get('recommendation', 'No action'))}</strong>: {sanitize_text(analysis.get('reason_for_fraud_risk', 'No additional info'))}</p>", unsafe_allow_html=True)

                # ————————————————————————————————
                # ✅ GENERATE & DOWNLOAD REPORT (TXT)
                # ————————————————————————————————
                st.markdown("<h3 style='color:#003366;'>💾 Download Report</h3>", unsafe_allow_html=True)

                # Build TXT report
                txt_content = f"""
Insurance Claim Analysis Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}

USER DESCRIPTION:
{user_text}

CLAIM SUMMARY
Type: {sanitize_text(analysis.get('claim_type', 'N/A'))}
Severity: {sanitize_text(analysis.get('severity', 'N/A'))}
Fraud Risk: {sanitize_text(analysis.get('fraud_risk', 'N/A'))}
Consistency: {sanitize_text(analysis.get('visual_story_consistency', 'N/A'))}

ITEMS DETECTED
Before: {', '.join([sanitize_text(i) for i in analysis.get('items_before', [])] or ['None'])}
Missing: {', '.join([sanitize_text(i) for i in analysis.get('missing_items', [])] or ['None'])}
Damaged: {', '.join([sanitize_text(i) for i in analysis.get('damaged_items', [])] or ['None'])}

AI ASSESSMENT
Reason for Fraud Risk: {sanitize_text(analysis.get('reason_for_fraud_risk', 'N/A'))}
Recommendation: {sanitize_text(analysis.get('recommendation', 'N/A'))}

---
AI-generated report — For internal use only.
"""

                # ✅ Fix Download Link
                b64_txt = base64.b64encode(txt_content.encode()).decode()
                filename = f"claim_report_{datetime.now().strftime('%H%M%S')}.txt"
                href = f'<a href="data:text/plain;base64,{b64_txt}" download="{filename}"><button style="background-color:#28a745; color:white; border:none; padding:10px 20px; border-radius:5px; cursor:pointer; font-size:16px;">📄 Download TXT Report</button></a>'
                st.markdown(href, unsafe_allow_html=True)

                # Show images
                st.markdown("<h3 style='color:#003366;'>🖼️ Image Comparison</h3>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    st.image(before_img, caption="Before Incident", use_column_width=True)
                with col2:
                    st.image(after_img, caption="After Incident", use_column_width=True)

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.code(str(e), language="text")

# ————————————————————————————————
# Footer
# ————————————————————————————————
st.markdown("---")
st.markdown("<p style='text-align:center; color:#666;'>Built with Google Gemini • For internal innovation</p>", unsafe_allow_html=True)