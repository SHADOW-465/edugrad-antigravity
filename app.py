import streamlit as st
import os
from ai_engine import AIGrader
from utils import save_uploaded_file, cleanup_temp_files
from PIL import Image

# Page Config
st.set_page_config(page_title="AI Answer Grader", layout="wide", page_icon="📝")

# Custom CSS for Mobile Friendliness and Aesthetics
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
    }
    .report-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .score-box {
        font-size: 2em;
        font-weight: bold;
        color: #2c3e50;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for Configuration
with st.sidebar:
    st.title("⚙️ Settings")
    api_key = st.text_input("Enter Gemini API Key", type="password")
    st.info("Get your key from Google AI Studio")
    
    selected_model = None
    if api_key:
        try:
            available_models = AIGrader.list_available_models(api_key)
            if available_models:
                selected_model = st.selectbox("Select AI Model", available_models, index=0)
            else:
                st.error("No suitable models found or API Key invalid.")
        except Exception as e:
            st.error(f"Error fetching models: {e}")

    st.divider()
    st.subheader("Exam Details")
    subject = st.text_input("Subject", "Physics")
    student_level = st.selectbox("Student Level", ["High School (10th)", "Higher Secondary (12th)", "College"])
    max_marks = st.number_input("Max Marks", value=100)

# Main Content
st.title("📝 AI Answer Sheet Grader")
st.write("Upload handwritten answer sheets for instant grading and personalized feedback.")

if not api_key:
    st.warning("Please enter your Gemini API Key in the sidebar to proceed.")
    st.stop()

if not selected_model:
    st.warning("Please select a model from the sidebar.")
    st.stop()

grader = AIGrader(api_key, selected_model)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Upload Answer Sheet")
    uploaded_file = st.file_uploader("Choose an image...", type=['jpg', 'jpeg', 'png'])
    
    st.subheader("2. Grading Criteria")
    question_paper = st.text_area("Paste Question Paper Text", height=100, placeholder="Q1. What is Newton's First Law? ...")
    answer_key = st.text_area("Paste Answer Key / Rubric", height=100, placeholder="A1. Definition of inertia... (2 marks)")

    if uploaded_file and question_paper and answer_key:
        st.image(uploaded_file, caption="Uploaded Answer Sheet", use_column_width=True)
        
        if st.button("🚀 Grade Answer Sheet"):
            with st.spinner("AI is analyzing handwriting and grading..."):
                # Save temp file
                file_path = save_uploaded_file(uploaded_file)
                
                if file_path:
                    # Call AI
                    result = grader.grade_submission(file_path, question_paper, answer_key, max_marks, student_level)
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.session_state['result'] = result
                        st.session_state['file_path'] = file_path
                        st.success("Grading Complete!")
                else:
                    st.error("File upload failed.")

with col2:
    if 'result' in st.session_state:
        result = st.session_state['result']
        
        st.subheader("3. Grading Report")
        
        # Report Card UI
        st.markdown(f"""
        <div class="report-card">
            <h3 style="text-align: center; margin-top: 0;">Student Report</h3>
            <div class="score-box">{result.get('total_score_obtained', 0)} / {result.get('max_score', 100)}</div>
            <p style="text-align: center;"><b>Student:</b> {result.get('student_name', 'Unknown')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed Breakdown
        with st.expander("View Detailed Question-wise Breakdown", expanded=True):
            for q in result.get('question_wise_breakdown', []):
                color = "green" if q['status'] == "Correct" else "orange" if q['status'] == "Partially Correct" else "red"
                st.markdown(f"**Q{q['question_number']}**: <span style='color:{color}'>{q['marks_obtained']}/{q['max_marks']}</span> - {q['status']}", unsafe_allow_html=True)
                st.caption(f"Feedback: {q['feedback']}")
                st.divider()

        # Feedback Section
        st.subheader("💡 Personalized Feedback")
        st.info(result.get('overall_feedback', 'No feedback provided.'))
        
        st.subheader("📈 Areas for Improvement")
        for point in result.get('improvement_pointers', []):
            st.markdown(f"- {point}")
            
        # Study Plan Generation
        st.divider()
        if st.button("🎓 Generate Study Plan & Real-world Context"):
            with st.spinner("Creating study plan..."):
                study_plan = grader.generate_study_plan(result)
                st.markdown(study_plan)

# Cleanup on session end (optional/manual)
# cleanup_temp_files()
