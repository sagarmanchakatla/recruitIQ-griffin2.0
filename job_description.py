# import re
# import json
# import groq
# import os
# from typing import Dict, Any, Optional

# class JobDescriptionAgent:
#     def __init__(self, api_key: Optional[str] = None):
#         """Initialize the job description agent with optional API key."""
#         self.api_key = api_key or os.environ.get("GROQ_API_KEY")
#         if not self.api_key:
#             raise ValueError("Groq API key is required. Set it as GROQ_API_KEY environment variable or pass it directly.")
#         self.client = groq.Groq(api_key=self.api_key)
#         self.model = "llama3-70b-8192"  # Default model

#     def analyze_job(self, company: str, title: str, description: str) -> Dict[str, Any]:
#         """
#         Analyze a job description and extract structured information.
#         """
#         prompt = f"""
#         Analyze the following job description and extract key information.

#         Company: {company}
#         Position: {title}
        
#         Description:
#         {description}
        
#         Extract and organize the following information in JSON format:
#         1. Summary: A concise 2-3 sentence summary of the position
#         2. Technical Skills: List all technical skills mentioned or implied
#         3. Soft Skills: List all soft skills/personal qualities mentioned or implied
#         4. Tools/Software: List any specific tools, software, platforms mentioned
#         5. Years of Experience: Extract any experience requirements (or indicate if not specified)
#         6. Education: Extract education requirements (or indicate if not specified)
#         7. Certifications: List any required or preferred certifications (or indicate if not specified)
#         8. Job Level: Entry, Mid, Senior, etc. based on the description
#         9. Primary Responsibilities: List 3-5 main job responsibilities
#         10. Industry: The industry this job is in
#         11. Remote/Onsite: Whether the job is remote, hybrid, or onsite (if mentioned)
#         12. Keywords: A list of 5-10 important keywords for this position
        
#         Return only the JSON object with these fields, nothing else.
#         """
        
#         try:
#             response = self.client.chat.completions.create(
#                 model=self.model,
#                 messages=[
#                     {"role": "system", "content": "You are a specialized job analysis assistant that extracts structured information from job descriptions accurately."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 temperature=0.1,
#                 max_tokens=2048
#             )
            
#             result_text = response.choices[0].message.content
            
#             # Extract JSON
#             try:
#                 json_match = re.search(r'({[\s\S]*})', result_text)
#                 if json_match:
#                     result_text = json_match.group(1)
#                 result = json.loads(result_text)
#                 result["Company"] = company
#                 result["Job Title"] = title
#                 return result
#             except json.JSONDecodeError:
#                 print("Error: Could not parse JSON from LLM response")
#                 print("Raw response:", result_text)
#                 return {"Error": "Failed to parse structured data from job description"}
                
#         except Exception as e:
#             print(f"Error calling Groq API: {e}")
#             return {"Error": str(e)}

#     def print_analysis(self, analysis: Dict[str, Any]) -> None:
#         """
#         Print the job analysis in a readable format.
#         """
#         if "Error" in analysis:
#             print(f"ERROR: {analysis['Error']}")
#             return

#         print("\n" + "="*50)
#         print(f"JOB ANALYSIS: {analysis.get('Company')} - {analysis.get('Job Title')}")
#         print("="*50)
        
#         print(f"\n📝 SUMMARY")
#         print(f"{analysis.get('Summary', 'Not specified')}")
        
#         print(f"\n🔧 TECHNICAL SKILLS")
#         for skill in analysis.get('Technical Skills', []):
#             print(f"• {skill}")
        
#         print(f"\n🤝 SOFT SKILLS")
#         for skill in analysis.get('Soft Skills', []):
#             print(f"• {skill}")
        
#         print(f"\n💻 TOOLS & SOFTWARE")
#         for tool in analysis.get('Tools/Software', []):
#             print(f"• {tool}")
        
#         print(f"\n🎓 EDUCATION")
#         print(f"{analysis.get('Education', 'Not specified')}")
        
#         print(f"\n⏱ EXPERIENCE")
#         print(f"{analysis.get('Years of Experience', 'Not specified')}")
        
#         print(f"\n🏆 CERTIFICATIONS")
#         for cert in analysis.get('Certifications', []):
#             print(f"• {cert}")
        
#         print(f"\n📋 PRIMARY RESPONSIBILITIES")
#         for resp in analysis.get('Primary Responsibilities', []):
#             print(f"• {resp}")
        
#         print(f"\n🏢 JOB DETAILS")
#         print(f"• Level: {analysis.get('Job Level', 'Not specified')}")
#         print(f"• Industry: {analysis.get('Industry', 'Not specified')}")
#         print(f"• Work Mode: {analysis.get('Remote/Onsite', 'Not specified')}")
        
#         print(f"\n🔑 KEYWORDS")
#         print(", ".join(analysis.get('Keywords', [])))
        
#         print("\n" + "="*50 + "\n")

# def main():
#     """Main function with hardcoded input."""

#     company = "Microsoft"
#     title = "Data Scientist"
#     description = """Job Description:
#     We are looking for a skilled Data Scientist to analyze complex datasets, develop predictive models, and provide actionable insights. You will collaborate with cross-functional teams to optimize business strategies and drive data-driven decision-making.

#     Responsibilities:
#     Collect, clean, and analyze large datasets.
#     Develop and deploy machine learning models.
#     Build predictive analytics solutions to improve business outcomes.
#     Communicate findings through reports and visualizations.
#     Stay updated with advancements in data science and AI.

#     Qualifications:
#     Bachelor’s or Master’s degree in Data Science, Computer Science, or a related field.
#     Proficiency in Python, R, SQL, and machine learning frameworks.
#     Experience with data visualization tools like Tableau or Power BI.
#     Strong analytical and problem-solving skills.
#     Ability to work independently and in a team environment."""

#     # API key can be set here or via environment variable
#     api_key = "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"  # or replace None with your "your-groq-api-key"

#     try:
#         agent = JobDescriptionAgent(api_key=api_key)
#         print(f"Analyzing job: {title} at {company}...\n")
#         analysis = agent.analyze_job(company, title, description)
#         agent.print_analysis(analysis)
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     main()



import re
import json
import sqlite3
import os
import groq
from typing import Dict, Any, Optional

class JobDescriptionAgent:
    def __init__(self, api_key: Optional[str] = None, db_path: str = "job_analysis.db"):
        """Initialize the job description agent with optional API key and database connection."""
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Set it as GROQ_API_KEY environment variable or pass it directly.")
        self.client = groq.Groq(api_key=self.api_key)
        self.model = "llama3-70b-8192"  # Default model

        # Setup database
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        """Create the jobs table if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                job_title TEXT,
                job_summary TEXT,
                technical_skills TEXT,
                soft_skills TEXT,
                tools_software TEXT,
                min_education TEXT,
                experience TEXT,
                certifications TEXT,
                primary_responsibilities TEXT,
                job_level TEXT,
                industry TEXT,
                work_mode TEXT,
                keywords TEXT,
                salary TEXT,
                location TEXT
            )
        ''')
        self.conn.commit()

    def analyze_job(self, company: str, title: str, description: str) -> Dict[str, Any]:
        """Analyze a job description and extract structured information."""
        prompt = f"""
        Analyze the following job description and extract key information.

        Company: {company}
        Position: {title}
        
        Description:
        {description}
        
        Extract and organize the following information in JSON format:
        1. Summary: A concise 2-3 sentence summary of the position
        2. Technical Skills: List all technical skills mentioned or implied
        3. Soft Skills: List all soft skills/personal qualities mentioned or implied
        4. Tools/Software: List any specific tools, software, platforms mentioned
        5. Years of Experience: Extract any experience requirements (or indicate if not specified)
        6. Education: Extract education requirements (or indicate if not specified)
        7. Certifications: List any required or preferred certifications (or indicate if not specified)
        8. Job Level: Entry, Mid, Senior, etc. based on the description
        9. Primary Responsibilities: List 3-5 main job responsibilities
        10. Industry: The industry this job is in
        11. Remote/Onsite: Whether the job is remote, hybrid, or onsite (if mentioned)
        12. Keywords: A list of 5-10 important keywords for this position
        13. Salary: Mention salary if available (else put 'Not specified')
        14. Location: Mention location if available (else put 'Not specified')

        Return only the JSON object with these fields, nothing else.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a specialized job analysis assistant that extracts structured information from job descriptions accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2048
            )
            
            result_text = response.choices[0].message.content
            
            # Extract JSON
            try:
                json_match = re.search(r'({[\s\S]*})', result_text)
                if json_match:
                    result_text = json_match.group(1)
                result = json.loads(result_text)
                result["Company"] = company
                result["Job Title"] = title
                return result
            except json.JSONDecodeError:
                print("Error: Could not parse JSON from LLM response")
                print("Raw response:", result_text)
                return {"Error": "Failed to parse structured data from job description"}
                
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return {"Error": str(e)}

    def save_to_db(self, analysis: Dict[str, Any]) -> None:
        """Save the analysis result into the database."""
        if "Error" in analysis:
            print(f"Skipping save due to error: {analysis['Error']}")
            return

        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO job_analysis (
                company, job_title, job_summary, technical_skills, soft_skills, tools_software,
                min_education, experience, certifications, primary_responsibilities, 
                job_level, industry, work_mode, keywords, salary, location
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis.get("Company"),
            analysis.get("Job Title"),
            analysis.get("Summary"),
            json.dumps(analysis.get("Technical Skills", [])),
            json.dumps(analysis.get("Soft Skills", [])),
            json.dumps(analysis.get("Tools/Software", [])),
            analysis.get("Education"),
            analysis.get("Years of Experience"),
            json.dumps(analysis.get("Certifications", [])),
            json.dumps(analysis.get("Primary Responsibilities", [])),
            analysis.get("Job Level"),
            analysis.get("Industry"),
            analysis.get("Remote/Onsite"),
            json.dumps(analysis.get("Keywords", [])),
            analysis.get("Salary", "Not specified"),
            analysis.get("Location", "Not specified")
        ))
        self.conn.commit()
        print("✅ Saved analysis to database!")

    def print_analysis(self, analysis: Dict[str, Any]) -> None:
        """Print the job analysis in a readable format."""
        if "Error" in analysis:
            print(f"ERROR: {analysis['Error']}")
            return

        print("\n" + "="*50)
        print(f"JOB ANALYSIS: {analysis.get('Company')} - {analysis.get('Job Title')}")
        print("="*50)
        
        print(f"\n📝 SUMMARY")
        print(f"{analysis.get('Summary', 'Not specified')}")
        
        print(f"\n🔧 TECHNICAL SKILLS")
        for skill in analysis.get('Technical Skills', []):
            print(f"• {skill}")
        
        print(f"\n🤝 SOFT SKILLS")
        for skill in analysis.get('Soft Skills', []):
            print(f"• {skill}")
        
        print(f"\n💻 TOOLS & SOFTWARE")
        for tool in analysis.get('Tools/Software', []):
            print(f"• {tool}")
        
        print(f"\n🎓 EDUCATION")
        print(f"{analysis.get('Education', 'Not specified')}")
        
        print(f"\n⏱ EXPERIENCE")
        print(f"{analysis.get('Years of Experience', 'Not specified')}")
        
        print(f"\n🏆 CERTIFICATIONS")
        for cert in analysis.get('Certifications', []):
            print(f"• {cert}")
        
        print(f"\n📋 PRIMARY RESPONSIBILITIES")
        for resp in analysis.get('Primary Responsibilities', []):
            print(f"• {resp}")
        
        print(f"\n🏢 JOB DETAILS")
        print(f"• Level: {analysis.get('Job Level', 'Not specified')}")
        print(f"• Industry: {analysis.get('Industry', 'Not specified')}")
        print(f"• Work Mode: {analysis.get('Remote/Onsite', 'Not specified')}")
        
        print(f"\n💰 SALARY")
        print(f"{analysis.get('Salary', 'Not specified')}")
        
        print(f"\n📍 LOCATION")
        print(f"{analysis.get('Location', 'Not specified')}")
        
        print(f"\n🔑 KEYWORDS")
        print(", ".join(analysis.get('Keywords', [])))
        
        print("\n" + "="*50 + "\n")

    def list_jobs(self):
        """List all jobs currently stored in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, company, job_title, location FROM job_analysis ORDER BY id DESC")
        jobs = cursor.fetchall()
        print("\n🗂️  SAVED JOBS:")
        print("-" * 40)
        for job in jobs:
            print(f"[{job[0]}] {job[1]} - {job[2]} ({job[3]})")
        print("-" * 40)
        print(f"Total Jobs Saved: {len(jobs)}\n")

def main():
    """Main function with hardcoded input."""
    company = "amazon"
    title = "Software Engineer"
    description = """We are seeking a skilled Software Engineer to design, develop, and maintain software applications.

    Responsibilities:

    Develop, test, and deploy software applications.
    Write clean, maintainable, and scalable code.
    Collaborate with cross-functional teams to define and implement features.
    Troubleshoot and debug issues for optimal performance.
    Stay updated with emerging technologies and best practices.
    Qualifications
    """


    api_key = "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"

    try:
        agent = JobDescriptionAgent(api_key=api_key)
        print(f"Analyzing job: {title} at {company}...\n")
        analysis = agent.analyze_job(company, title, description)
        agent.print_analysis(analysis)
        agent.save_to_db(analysis)
        agent.list_jobs()  # 🎯 See all jobs saved after inserting
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
