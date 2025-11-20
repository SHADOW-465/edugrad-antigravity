import streamlit as st
import os
from ai_engine import AIGrader
from database import DatabaseManager
from utils import save_uploaded_file, cleanup_temp_files
import json

# Page Config
st.set_page_config(page_title="AI Answer Grader", layout="wide", page_icon="📝")

# Initialize DB
if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()

db = st.session_state.db

# Custom CSS
st.markdown("""
<style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #4CAF50; color: white; }
    .report-card { background-color: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .score-box { font-size: 2em; font-weight: bold; color: #2c3e50; text-align: center; }
    .status-graded { color: green; font-weight: bold; }
    .status-pending { color: orange; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Auth & Settings ---
with st.sidebar:
    st.title("🏫 AI School Grader")
    
    # API Key
    api_key = st.text_input("Gemini API Key", type="password")
    if not api_key:
        st.warning("Enter API Key to proceed.")
        st.stop()
        
    # Model Selection
    selected_model = None
    try:
        available_models = AIGrader.list_available_models(api_key)
        if available_models:
            selected_model = st.selectbox("AI Model", available_models, index=0)
        else:
            st.error("No models found.")
    except:
        pass

    st.divider()
    
    # Role Selection
    role = st.radio("Login As", ["Teacher", "Parent/Student"])

# --- Teacher Dashboard ---
if role == "Teacher":
    st.header("👨‍🏫 Teacher Dashboard")
    
    tab1, tab2, tab3 = st.tabs(["Manage Classes", "Create Exam", "Grading & Results"])
    
    # 1. Manage Classes
    with tab1:
        st.subheader("Create New Class")
        with st.form("create_class"):
            c_name = st.text_input("Class Name (e.g., 10-A)")
            c_level = st.selectbox("Grade Level", ["High School", "Higher Secondary", "College"])
            if st.form_submit_button("Create Class"):
                db.create_class(c_name, c_level)
                st.success(f"Class {c_name} created!")
        
        st.subheader("Add Student to Class")
        classes = db.get_all_classes()
        if classes:
            c_options = {c[1]: c[0] for c in classes}
            selected_class_name = st.selectbox("Select Class", list(c_options.keys()))
            selected_class_id = c_options[selected_class_name]
            
            with st.form("add_student"):
                s_name = st.text_input("Student Name")
                s_roll = st.text_input("Roll Number")
                if st.form_submit_button("Add Student"):
                    db.add_student(s_name, s_roll, selected_class_id)
                    st.success(f"Student {s_name} added!")
        else:
            st.info("No classes found. Create one first.")

    # 2. Create Exam
    with tab2:
        st.subheader("Schedule New Exam")
        if classes:
            with st.form("create_exam"):
                e_name = st.text_input("Exam Name (e.g., Physics Mid-Term)")
                e_subject = st.text_input("Subject")
                e_class = st.selectbox("For Class", list(c_options.keys()), key="exam_class")
                e_max = st.number_input("Max Marks", value=100)
                e_qp = st.text_area("Paste Question Paper Text")
                e_key = st.text_area("Paste Answer Key / Rubric")
                
                if st.form_submit_button("Create Exam"):
                    cid = c_options[e_class]
                    db.create_exam(e_name, e_subject, cid, e_qp, e_key, e_max)
                    st.success(f"Exam {e_name} created!")
        else:
            st.warning("Create a class first.")

    # 3. Grading & Results
    with tab3:
        st.subheader("Grading Interface")
        
        # Select Class -> Exam
        if classes:
            sel_class_grad = st.selectbox("Select Class", list(c_options.keys()), key="grad_class")
            cid_grad = c_options[sel_class_grad]
            exams = db.get_exams_by_class(cid_grad)
            
            if exams:
                exam_opts = {e[1]: e for e in exams}
                sel_exam_name = st.selectbox("Select Exam", list(exam_opts.keys()))
                selected_exam = exam_opts[sel_exam_name] # (id, name, subj, cid, qp, key, max)
                exam_id = selected_exam[0]
                
                # List Students
                students = db.get_students_by_class(cid_grad)
                
                st.divider()
                st.markdown(f"### Grading: {sel_exam_name}")
                
                # Strictness Control
                strictness = st.select_slider("Grading Strictness", options=["Lenient", "Moderate", "Strict"], value="Moderate")
                
                # Per Student Row
                for stu in students: # (id, name, roll, cid)
                    stu_id = stu[0]
                    stu_name = stu[1]
                    
                    with st.expander(f"{stu_name} ({stu[2]})", expanded=False):
                        col_up, col_act = st.columns([2, 1])
                        
                        # Check submission status
                        sub = db.get_submission(exam_id, stu_id)
                        status = sub[6] if sub else "Not Uploaded"
                        
                        with col_up:
                            st.write(f"Status: **{status}**")
                            upl_file = st.file_uploader(f"Upload Answer Sheet for {stu_name}", type=['jpg', 'png'], key=f"u_{stu_id}")
                        
                        with col_act:
                            if upl_file and selected_model:
                                if st.button(f"Grade {stu_name}", key=f"g_{stu_id}"):
                                    with st.spinner("Grading..."):
                                        # Save file
                                        fpath = save_uploaded_file(upl_file)
                                        if fpath:
                                            grader = AIGrader(api_key, selected_model)
                                            res = grader.grade_submission(
                                                fpath, 
                                                selected_exam[4], # QP
                                                selected_exam[5], # Key
                                                selected_exam[6], # Max
                                                strictness=strictness
                                            )
                                            if "error" not in res:
                                                db.save_submission(exam_id, stu_id, fpath, res)
                                                st.success("Graded!")
                                                st.rerun()
                                            else:
                                                st.error(res['error'])
                        
                        # Show Result if Graded
                        if sub and sub[4]: # grades_json
                            grades = json.loads(sub[4])
                            st.info(f"Score: {grades.get('total_score_obtained')} / {grades.get('max_score')}")
                            st.write(f"**Feedback:** {grades.get('overall_feedback')}")
                            if st.button("View Full Report", key=f"v_{stu_id}"):
                                st.json(grades)

                st.divider()
                if st.button("📢 Publish All Results to Parents"):
                    db.publish_results(exam_id)
                    st.success("Results Published!")
            else:
                st.info("No exams found for this class.")

# --- Parent Dashboard ---
elif role == "Parent/Student":
    st.header("👨‍👩‍👧 Parent Dashboard")
    
    # Mock Login: Select Student
    # In real app, this would be secure login
    all_classes = db.get_all_classes()
    if all_classes:
        c_opts = {c[1]: c[0] for c in all_classes}
        p_class = st.selectbox("Select Class", list(c_opts.keys()))
        p_cid = c_opts[p_class]
        
        p_students = db.get_students_by_class(p_cid)
        if p_students:
            s_opts = {s[1]: s[0] for s in p_students}
            p_student_name = st.selectbox("Select Student Name", list(s_opts.keys()))
            p_sid = s_opts[p_student_name]
            
            st.divider()
            st.subheader(f"Results for {p_student_name}")
            
            results = db.get_student_results(p_sid) # (id, exam_name, subject, grades_json, status)
            
            if results:
                for res in results:
                    exam_name = res[1]
                    subject = res[2]
                    grades = json.loads(res[3])
                    
                    with st.expander(f"{exam_name} - {subject}", expanded=True):
                        st.markdown(f"""
                        <div class="report-card">
                            <div class="score-box">{grades.get('total_score_obtained')} / {grades.get('max_score')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.subheader("Feedback")
                        st.write(grades.get('overall_feedback'))
                        
                        st.subheader("Real World Connections 🌍")
                        st.info(grades.get('real_world_connections', 'Not available'))
                        
                        st.subheader("Areas for Improvement")
                        for p in grades.get('improvement_pointers', []):
                            st.markdown(f"- {p}")
            else:
                st.info("No published results yet.")
        else:
            st.info("No students in this class.")
