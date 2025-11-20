import sqlite3
import json

class DatabaseManager:
    def __init__(self, db_name="school_grades.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Classes Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade_level TEXT NOT NULL
        )
        ''')

        # Students Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT NOT NULL,
            class_id INTEGER,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
        ''')

        # Exams Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject TEXT NOT NULL,
            class_id INTEGER,
            question_paper_text TEXT,
            answer_key_text TEXT,
            max_marks INTEGER,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
        ''')

        # Submissions Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER,
            student_id INTEGER,
            image_path TEXT,
            grades_json TEXT,
            teacher_feedback TEXT,
            status TEXT DEFAULT 'Pending', -- Pending, Graded, Published
            FOREIGN KEY (exam_id) REFERENCES exams (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
        ''')
        self.conn.commit()

    # --- Class Methods ---
    def create_class(self, name, grade_level):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO classes (name, grade_level) VALUES (?, ?)", (name, grade_level))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_classes(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM classes")
        return cursor.fetchall()

    def get_class_by_id(self, class_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM classes WHERE id = ?", (class_id,))
        return cursor.fetchone()

    # --- Student Methods ---
    def add_student(self, name, roll_number, class_id):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO students (name, roll_number, class_id) VALUES (?, ?, ?)", (name, roll_number, class_id))
        self.conn.commit()

    def get_students_by_class(self, class_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE class_id = ?", (class_id,))
        return cursor.fetchall()
    
    def get_student_by_id(self, student_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        return cursor.fetchone()

    # --- Exam Methods ---
    def create_exam(self, name, subject, class_id, qp_text, ans_key_text, max_marks):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO exams (name, subject, class_id, question_paper_text, answer_key_text, max_marks) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, subject, class_id, qp_text, ans_key_text, max_marks))
        self.conn.commit()
        return cursor.lastrowid

    def get_exams_by_class(self, class_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM exams WHERE class_id = ?", (class_id,))
        return cursor.fetchall()

    def get_exam_by_id(self, exam_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM exams WHERE id = ?", (exam_id,))
        return cursor.fetchone()

    # --- Submission Methods ---
    def get_submission(self, exam_id, student_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM submissions WHERE exam_id = ? AND student_id = ?", (exam_id, student_id))
        return cursor.fetchone()

    def save_submission(self, exam_id, student_id, image_path, grades_json, status="Graded"):
        cursor = self.conn.cursor()
        # Check if exists
        existing = self.get_submission(exam_id, student_id)
        if existing:
            cursor.execute("""
                UPDATE submissions 
                SET image_path = ?, grades_json = ?, status = ?
                WHERE id = ?
            """, (image_path, json.dumps(grades_json), status, existing[0]))
        else:
            cursor.execute("""
                INSERT INTO submissions (exam_id, student_id, image_path, grades_json, status)
                VALUES (?, ?, ?, ?, ?)
            """, (exam_id, student_id, image_path, json.dumps(grades_json), status))
        self.conn.commit()

    def publish_results(self, exam_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE submissions SET status = 'Published' WHERE exam_id = ?", (exam_id,))
        self.conn.commit()
        
    def get_student_results(self, student_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT s.id, e.name, e.subject, s.grades_json, s.status 
            FROM submissions s
            JOIN exams e ON s.exam_id = e.id
            WHERE s.student_id = ? AND s.status = 'Published'
        """, (student_id,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()
