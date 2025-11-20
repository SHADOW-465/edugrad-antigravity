import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from PIL import Image

load_dotenv()

class AIGrader:
    def __init__(self, api_key, model_name):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    @staticmethod
    def list_available_models(api_key):
        """
        Lists available Gemini models that support content generation.
        """
        try:
            genai.configure(api_key=api_key)
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name)
            models.sort(reverse=True) 
            return models
        except Exception as e:
            return []

    def grade_submission(self, image_path, question_paper, answer_key, max_marks, student_name, student_level="High School", strictness="Moderate", language="English"):
        """
        Grades the answer sheet image against the provided context with strictness control and language support.
        """
        
        img = Image.open(image_path)

        strictness_prompt = ""
        if strictness == "Strict":
            strictness_prompt = "Be very strict. Deduct marks for minor errors, spelling mistakes, and lack of clarity. Expect high precision."
        elif strictness == "Lenient":
            strictness_prompt = "Be lenient. Award marks for partial understanding and effort. Ignore minor spelling or grammatical errors if the concept is understood."
        else:
            strictness_prompt = "Be moderate. Balance precision with understanding. Grade fairly based on the rubric."

        lang_prompt = ""
        if language == "Tamil":
            lang_prompt = "Provide the 'overall_feedback', 'improvement_pointers', and 'real_world_connections' in Tamil language. Keep technical terms in English if needed for clarity, but the explanation should be in Tamil."
        else:
            lang_prompt = "Provide all feedback and explanations in English."

        prompt = f"""
        You are an expert academic grader for {student_level} students in Tamil Nadu, India. 
        Your task is to grade the handwritten answer sheet provided in the image.
        
        **Student Name:** {student_name} (Use this name in the report)
        **Grading Mode:** {strictness}
        {strictness_prompt}
        
        **Language Requirement:**
        {lang_prompt}
        
        **Context:**
        - Question Paper: {question_paper}
        - Answer Key / Rubric: {answer_key}
        - Maximum Marks: {max_marks}
        
        **Instructions:**
        1. **Analyze the Image**: Read the handwritten answers carefully. Handle messy handwriting gracefully.
        2. **Grade**: Assign marks for each question based on the Answer Key and the Grading Mode.
        3. **Feedback**: Provide specific feedback for each answer. Point out what was correct and what was missing.
        4. **Improvement**: Suggest how the student can improve for next time.
        5. **Real World Context**: For every major concept, explain its importance in real life.
        6. **Output Format**: Return the result strictly in JSON format.
        
        **JSON Structure:**
        {{
            "student_name": "{student_name}",
            "total_score_obtained": float,
            "max_score": {max_marks},
            "question_wise_breakdown": [
                {{
                    "question_number": "1",
                    "marks_obtained": float,
                    "max_marks": float,
                    "feedback": "Specific feedback for this answer",
                    "status": "Correct/Partially Correct/Incorrect"
                }}
            ],
            "overall_feedback": "General summary of performance",
            "improvement_pointers": [
                "Point 1",
                "Point 2"
            ],
            "concepts_to_revise": [
                "Concept 1",
                "Concept 2"
            ],
            "real_world_connections": "A short paragraph explaining the real-world importance of the topics covered in this exam."
        }}
        """

        try:
            response = self.model.generate_content([prompt, img])
            text_response = response.text.strip()
            if text_response.startswith("```json"):
                text_response = text_response[7:-3]
            elif text_response.startswith("```"):
                text_response = text_response[3:-3]
            return json.loads(text_response)
        except Exception as e:
            return {"error": str(e)}

    def generate_study_plan(self, grading_result, language="English"):
        """
        Generates a personalized study plan based on the grading result.
        """
        lang_prompt = "in Tamil" if language == "Tamil" else "in English"
        
        prompt = f"""
        Based on the following grading result, create a short, motivating study plan for the student {lang_prompt}.
        Focus on the 'concepts_to_revise'. Explain *why* these concepts are important in real life (connect to real world applications).
        
        Grading Result:
        {json.dumps(grading_result)}
        
        Output Format: Markdown
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return "Could not generate study plan."
