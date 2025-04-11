# # streamlit_app.py
# import sys
# import os
# import random
# from pathlib import Path

# # Add the parent directory to sys.path
# sys.path.append(str(Path(__file__).resolve().parent.parent))

# # Now you can import
# import job_matcher

# import streamlit as st
# import pandas as pd
# import tempfile

# # Constants
# DB_PATH = "../job_analysis.db"
# API_KEY = "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"

# # Placeholder Images (random pics)
# PLACEHOLDER_IMAGES = [
#     "https://source.unsplash.com/400x300/?career",
#     "https://source.unsplash.com/400x300/?office",
#     "https://source.unsplash.com/400x300/?work",
#     "https://source.unsplash.com/400x300/?job",
#     "https://source.unsplash.com/400x300/?technology",
#     "https://source.unsplash.com/400x300/?startup"
# ]

# # Streamlit Page Config
# st.set_page_config(page_title="Resume Matcher", page_icon="🧠", layout="wide")

# # Tabs
# tab1, tab2 = st.tabs(["🎯 Resume Matcher", "📋 All Jobs Board"])

# # ---------------------------------
# # Tab 1: Resume Matcher
# # ---------------------------------
# with tab1:
#     st.title("🧠 Resume Matcher using Gemini AI")
#     st.subheader("Upload your Resume and get the Best Job Matches!")

#     # Upload Resume
#     uploaded_file = st.file_uploader("Upload your resume (PDF format)", type=["pdf"])

#     if uploaded_file:
#         # Save the uploaded file to a temporary location
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
#             tmp_file.write(uploaded_file.read())
#             resume_path = Path(tmp_file.name)

#         # Initialize Job Finder
#         job_finder = job_matcher.JobFinder(DB_PATH)

#         # Analyze Resume and Find Best Jobs
#         with st.spinner("Processing your resume... This may take a few seconds..."):
#             try:
#                 best_jobs = job_finder.find_best_jobs_from_pdf(resume_path, api_key=API_KEY)

#                 if best_jobs is not None and not best_jobs.empty:
#                     st.success("✅ Here are your best matches!")
                    
#                     for idx, row in best_jobs.iterrows():
#                         with st.expander(f"🎯 {row['job_title']} at {row['company']} - Score: {row['match_score']}%"):
#                             st.markdown(f"**Recommendation:** {row['recommendation']}")
#                             st.markdown("**Strengths:**")
#                             for strength in row['strengths']:
#                                 st.markdown(f"- ✅ {strength}")
#                             st.markdown("**Weaknesses:**")
#                             for weakness in row['weaknesses']:
#                                 st.markdown(f"- ⚠️ {weakness}")
#                 else:
#                     st.warning("No good matches found. Try another resume.")

#             except Exception as e:
#                 st.error(f"Something went wrong: {e}")

#             finally:
#                 job_finder.close()

#         # Clean up temporary file
#         os.unlink(resume_path)

# # ---------------------------------
# # Tab 2: All Jobs Board
# # ---------------------------------
# with tab2:
#     st.title("📋 All Available Jobs")
#     st.subheader("Explore all the open job opportunities!")

#     # Initialize Job Finder
#     job_finder = job_matcher.JobFinder(DB_PATH)

#     try:
#         all_jobs = job_finder.get_all_jobs()

#         if all_jobs is not None and not all_jobs.empty:
#             for idx, row in all_jobs.iterrows():
#                 with st.container():
#                     cols = st.columns([1, 3])
                    
#                     # Random image
#                     with cols[0]:
#                         img_url = random.choice(PLACEHOLDER_IMAGES)
#                         st.image(img_url, use_container_width =True)
                    
#                     # Job details
#                     with cols[1]:
#                         st.subheader(f"{row['job_title']} at {row['company']}")
#                         st.markdown(f"📍 **Location:** {row.get('location', 'Unknown')}")
#                         st.markdown(f"📝 **Description:** {row.get('job_summary', 'No description available.')}")
#                         st.markdown(f"📅 **Posted On:** {row.get('posted_date', 'N/A')}")
#                         st.divider()

#         else:
#             st.info("No jobs found in the database.")

#     except Exception as e:
#         st.error(f"Could not fetch jobs: {e}")

#     finally:
#         job_finder.close()

# # Footer
# st.markdown("---")
# st.caption("Built with ❤️ using Streamlit, Gemini, and Llama AI")


import sys
import os
import random
import smtplib
import ssl
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sqlite3
from datetime import datetime
import tempfile

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Now you can import
import job_matcher

import streamlit as st
import pandas as pd

# Constants
DB_PATH = "../job_analysis.db"
API_KEY = "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"
RECRUITER_DB = "recruiter_db.db"

# Email Configuration
SMTP_CONFIG = {
    'sender_email': 'zoyah768@gmail.com',
    'sender_password': 'ksha odyf dfyw eptm',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

# Initialize database
def init_db():
    conn = sqlite3.connect(RECRUITER_DB)
    c = conn.cursor()
    
    # Candidates table
    c.execute('''CREATE TABLE IF NOT EXISTS candidates
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  email TEXT NOT NULL,
                  phone TEXT,
                  resume_path TEXT,
                  status TEXT DEFAULT 'New',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Interviews table
    c.execute('''CREATE TABLE IF NOT EXISTS interviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  candidate_id INTEGER NOT NULL,
                  job_id TEXT NOT NULL,
                  job_title TEXT NOT NULL,
                  company TEXT NOT NULL,
                  scheduled_time TEXT NOT NULL,
                  status TEXT DEFAULT 'Scheduled',
                  notes TEXT,
                  FOREIGN KEY (candidate_id) REFERENCES candidates (id))''')
    
    conn.commit()
    conn.close()

init_db()

# Streamlit Page Config
st.set_page_config(page_title="Recruiter AI Assistant", page_icon="👔", layout="wide")

# Email functions
def send_interview_email(candidate_email, job_title, company, interview_time):
    """Send interview invitation email"""
    subject = f"Interview Invitation for {job_title} at {company}"
    body = f"""Dear Candidate,

We're pleased to invite you for an interview regarding the {job_title} position at {company}.

Interview Details:
- Date/Time: {interview_time}
- Location: Virtual (Zoom)

Please confirm your availability by replying to this email.

Best regards,
Recruitment Team
"""
    
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_CONFIG['sender_email']
        msg['To'] = candidate_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_CONFIG['smtp_server'], SMTP_CONFIG['smtp_port']) as server:
            server.starttls(context=context)
            server.login(SMTP_CONFIG['sender_email'], SMTP_CONFIG['sender_password'])
            server.sendmail(SMTP_CONFIG['sender_email'], candidate_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

# Tabs
tab1, tab2, tab3 = st.tabs(["🧠 AI Resume Matcher", "📋 Job Board", "📅 Interview Scheduler"])

# ---------------------------------
# Tab 1: AI Resume Matcher (Recruiter View)
# ---------------------------------
with tab1:
    st.title("AI-Powered Candidate Matcher")
    st.subheader("Upload candidate resumes to find best job matches")
    
    uploaded_file = st.file_uploader("Upload Candidate Resume (PDF)", type=["pdf"])
    
    if uploaded_file:
        with st.spinner("Analyzing resume..."):
            try:
                # Save resume temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    resume_path = Path(tmp_file.name)
                
                # Extract candidate info (you would enhance this with proper parsing)
                candidate_name = st.text_input("Candidate Name", "John Doe")
                candidate_email = st.text_input("Candidate Email", "john.doe@example.com")
                candidate_phone = st.text_input("Phone Number", "+1234567890")
                
                # Find matching jobs
                job_finder = job_matcher.JobFinder(DB_PATH)
                best_jobs = job_finder.find_best_jobs_from_pdf(resume_path, api_key=API_KEY)
                
                if best_jobs is not None and not best_jobs.empty:
                    st.success(f"Found {len(best_jobs)} matching jobs!")
                    
                    # Save candidate to database
                    conn = sqlite3.connect(RECRUITER_DB)
                    c = conn.cursor()
                    c.execute('''INSERT INTO candidates 
                                (name, email, phone, resume_path)
                                VALUES (?, ?, ?, ?)''',
                             (candidate_name, candidate_email, candidate_phone, str(resume_path)))
                    candidate_id = c.lastrowid
                    conn.commit()
                    conn.close()
                    
                    # Display matches
                    for idx, row in best_jobs.iterrows():
                        with st.expander(f"{row['job_title']} at {row['company']} - Match: {row['match_score']}%"):
                            st.markdown(f"*Recommendation:* {row['recommendation']}")
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("*Strengths:*")
                                for strength in row['strengths']:
                                    st.markdown(f"- ✅ {strength}")
                            with col2:
                                st.markdown("*Weaknesses:*")
                                for weakness in row['weaknesses']:
                                    st.markdown(f"- ⚠ {weakness}")
                            
                            if st.button("Schedule Interview", key=f"schedule_{idx}"):
                                st.session_state['schedule_for'] = {
                                    'candidate_id': candidate_id,
                                    'candidate_name': candidate_name,
                                    'candidate_email': candidate_email,
                                    'job_id': row.get('job_id', ''),
                                    'job_title': row['job_title'],
                                    'company': row['company'],
                                    'match_score': row['match_score']
                                }
                                st.session_state['current_tab'] = 'tab3'
                                st.rerun()
                else:
                    st.warning("No strong matches found for this candidate")
                
                os.unlink(resume_path)
                job_finder.close()
                
            except Exception as e:
                st.error(f"Error processing resume: {str(e)}")

# ---------------------------------
# Tab 2: Job Board (Recruiter View)
# ---------------------------------
with tab2:
    st.title("Job Position Management")
    
    # Add new job form
    with st.expander("➕ Add New Job Position"):
        with st.form("job_form"):
            title = st.text_input("Job Title")
            company = st.text_input("Company")
            location = st.text_input("Location")
            description = st.text_area("Description")
            requirements = st.text_area("Requirements")
            
            if st.form_submit_button("Save Job"):
                # In a real app, you'd save to your jobs database
                st.success(f"Added {title} at {company}")
    
    # View existing jobs
    st.subheader("Current Job Openings")
    try:
        job_finder = job_matcher.JobFinder(DB_PATH)
        all_jobs = job_finder.get_all_jobs()
        
        if all_jobs is not None and not all_jobs.empty:
            for idx, row in all_jobs.iterrows():
                with st.container():
                    st.subheader(f"{row['job_title']} at {row['company']}")
                    st.caption(f"📍 {row.get('location', 'Remote')} | 📅 Posted: {row.get('posted_date', 'N/A')}")
                    st.write(row.get('job_summary', 'No description available.'))
                    
                    # Show applicants button
                    if st.button("View Applicants", key=f"view_applicants_{idx}"):
                        # In a real app, you'd query applicants for this job
                        st.info(f"Showing applicants for {row['job_title']}")
                    st.divider()
        else:
            st.info("No jobs found in the database")
            
        job_finder.close()
    except Exception as e:
        st.error(f"Could not fetch jobs: {str(e)}")

# ---------------------------------
# Tab 3: Interview Scheduler
# ---------------------------------
with tab3:
    st.title("Interview Scheduling")
    
    if 'schedule_for' in st.session_state:
        candidate = st.session_state['schedule_for']
        st.subheader(f"Schedule Interview for {candidate['candidate_name']}")
        st.write(f"📧 {candidate['candidate_email']}")
        st.write(f"Position: {candidate['job_title']} at {candidate['company']}")
        st.write(f"Match Score: {candidate['match_score']}%")
        
        with st.form("interview_form"):
            interview_date = st.date_input("Date", min_value=datetime.now().date())
            interview_time = st.time_input("Time")
            interview_notes = st.text_area("Notes")
            
            if st.form_submit_button("Confirm Schedule"):
                scheduled_time = f"{interview_date} {interview_time}"
                
                # Save to database
                conn = sqlite3.connect(RECRUITER_DB)
                c = conn.cursor()
                c.execute('''INSERT INTO interviews
                            (candidate_id, job_id, job_title, company, scheduled_time, notes)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (candidate['candidate_id'],
                          candidate['job_id'],
                          candidate['job_title'],
                          candidate['company'],
                          scheduled_time,
                          interview_notes))
                
                # Update candidate status
                c.execute('''UPDATE candidates SET status='Interview Scheduled' 
                            WHERE id=?''', (candidate['candidate_id'],))
                
                conn.commit()
                conn.close()
                
                # Send email
                if send_interview_email(candidate['candidate_email'],
                                      candidate['job_title'],
                                      candidate['company'],
                                      scheduled_time):
                    st.success("✅ Interview scheduled and email sent!")
                    del st.session_state['schedule_for']
                else:
                    st.error("Interview scheduled but failed to send email")
    else:
        # View scheduled interviews
        st.subheader("Upcoming Interviews")
        conn = sqlite3.connect(RECRUITER_DB)
        c = conn.cursor()
        c.execute('''SELECT i.id, c.name, i.job_title, i.company, i.scheduled_time, i.status
                     FROM interviews i
                     JOIN candidates c ON i.candidate_id = c.id
                     ORDER BY i.scheduled_time''')
        interviews = c.fetchall()
        conn.close()
        
        if interviews:
            for interview in interviews:
                with st.expander(f"{interview[2]} with {interview[1]}"):
                    st.write(f"🏢 {interview[3]}")
                    st.write(f"⏰ {interview[4]}")
                    st.write(f"📌 Status: {interview[5]}")
                    
                    if st.button("Reschedule", key=f"reschedule_{interview[0]}"):
                        # Implement rescheduling logic
                        st.info("Rescheduling functionality would go here")
        else:
            st.info("No interviews scheduled yet")

# Footer
st.markdown("---")
st.caption("Recruiter AI Assistant v1.0 | Secure Hiring Platform")