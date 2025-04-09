import json
import sqlite3
import pandas as pd
from pathlib import Path
from resume_agent import extract_text_from_pdf, extract_keywords
import sys
import re
import google.generativeai as genai
import os

# Configure Gemini API
genai.configure(api_key="AIzaSyCUVb68DfmAYqdrWAZflhqkXxwoUeAyxB4")

class JobFinder:
    def __init__(self, db_path):
        """Initialize the JobFinder with the SQLite database path"""
        self.db_path = db_path
        self.conn = self._connect_to_db()
        
    def _connect_to_db(self):
        """Establish connection to SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            return conn
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            raise

    def _load_jobs_data(self):
        """Load jobs data from SQLite database"""
        query = """
        SELECT id, company, job_title, job_summary, 
               technical_skills, soft_skills, tools_software,
               min_education, experience, certifications,
               primary_responsibilities, job_level, industry,
               work_mode, keywords, salary, location
        FROM job_analysis
        """
        try:
            df = pd.read_sql(query, self.conn)
            # Convert string representations of lists to actual lists
            for col in ['technical_skills', 'soft_skills', 'tools_software', 
                        'primary_responsibilities', 'keywords']:
                df[col] = df[col].apply(lambda x: eval(x) if pd.notna(x) else [])
            # Parse certifications
            df['certifications'] = df['certifications'].apply(
                lambda x: eval(x) if pd.notna(x) and x.startswith('[') else 
                         ([x] if pd.notna(x) and x.strip('"') != "Not specified" else [])
            )
            return df
        except Exception as e:
            print(f"Error loading jobs data: {e}")
            raise

    def _parse_keywords(self, keywords_json):
        """Parse extracted keywords from resume agent"""
        try:
            if not keywords_json.strip().startswith('{'):
                start_idx = keywords_json.find('{')
                end_idx = keywords_json.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    keywords_json = keywords_json[start_idx:end_idx]
            return json.loads(keywords_json)
        except json.JSONDecodeError:
            return {
                'Technical Skills': [],
                'Soft Skills': [],
                'Tools/Software': [],
                'Industry Knowledge': [],
                'Certifications': [],
                'Education': []
            }

    def _normalize_text(self, text):
        """Normalize text by removing extra spaces and lowering"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip().lower())

    def _prepare_job_summary(self, job):
        """Prepare a compact job dictionary for Gemini"""
        return {
            "Company": job['company'],
            "Job Title": job['job_title'],
            "Job Summary": job['job_summary'],
            "Technical Skills": job['technical_skills'],
            "Soft Skills": job['soft_skills'],
            "Tools/Software": job['tools_software'],
            "Minimum Education": job['min_education'],
            "Experience": job['experience'],
            "Certifications": job['certifications'],
            "Primary Responsibilities": job['primary_responsibilities'],
            "Industry": job['industry'],
            "Work Mode": job['work_mode'],
            "Keywords": job['keywords'],
            "Salary": job['salary'],
            "Location": job['location']
        }

    def calculate_match_score_with_gemini(self, candidate_data, job_summary):
        """Use Gemini to calculate the match score between a candidate and a job"""
        prompt = f"""
You are a specialized AI matching agent. Based on the following information:

Job Description:
{json.dumps(job_summary, indent=2)}

Candidate Profile:
{json.dumps(candidate_data, indent=2)}

Calculate:
- match_score (0 to 100)
- strengths (list)
- weaknesses (list)
- recommendation (Interview / Consider / Reject)

Output only JSON like this:
{{
  "match_score": 85,
  "strengths": ["Skill match", "Good certifications"],
  "weaknesses": ["Less experience in cloud"],
  "recommendation": "Interview"
}}
"""

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)

        try:
            response_text = response.text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
        except Exception as e:
            print(f"Error parsing Gemini response: {e}")

        return {
            "match_score": 0,
            "strengths": [],
            "weaknesses": ["Error parsing Gemini response"],
            "recommendation": "Reject"
        }

    def find_best_jobs(self, resume_keywords_json, top_n=5):
        """Find best matching jobs using Gemini"""
        resume_keywords = self._parse_keywords(resume_keywords_json)
        jobs_df = self._load_jobs_data()

        results = []
        for _, job in jobs_df.iterrows():
            job_summary = self._prepare_job_summary(job)
            match_info = self.calculate_match_score_with_gemini(resume_keywords, job_summary)
            results.append({
                'id': job['id'],
                'company': job['company'],
                'job_title': job['job_title'],
                'match_score': match_info.get('match_score', 0),
                'recommendation': match_info.get('recommendation', 'Reject'),
                'strengths': match_info.get('strengths', []),
                'weaknesses': match_info.get('weaknesses', [])
            })

        # Convert results to DataFrame
        result_df = pd.DataFrame(results)
        result_df = result_df.sort_values(by='match_score', ascending=False).head(top_n)
        return result_df

    def find_best_jobs_from_pdf(self, pdf_path, api_key, top_n=5):
        """Extract resume text, analyze it, and find best jobs"""
        print(f"Extracting text from {pdf_path}...")
        resume_text = extract_text_from_pdf(pdf_path)
        
        print("Analyzing resume with Llama model...")
        keywords_output = extract_keywords(resume_text, api_key)

        if not keywords_output:
            print("Failed to extract keywords from resume.")
            return None
            
        return self.find_best_jobs(keywords_output, top_n)

    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()

def main():
    current_dir = Path(__file__).parent
    pdf_path = current_dir / "resume.pdf"
    db_path = current_dir / "job_analysis.db"
    api_key = "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"

    if not pdf_path.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
    
    if not db_path.exists():
        print(f"Error: Jobs database not found at {db_path}")
        sys.exit(1)
    
    job_finder = JobFinder(db_path)
    try:
        best_jobs = job_finder.find_best_jobs_from_pdf(pdf_path, api_key)
        
        if best_jobs is not None:
            print("\nTop Matching Jobs:")
            print(best_jobs.to_string(index=False))
    finally:
        job_finder.close()

if __name__ == "__main__":
    main()
