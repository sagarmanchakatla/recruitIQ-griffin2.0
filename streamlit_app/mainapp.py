import re
from email.mime.application import MIMEApplication
import sys
import os
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
DB_PATH = "main.db"  # Using only one database
API_KEY = "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"

# Email Configuration
SMTP_CONFIG = {
    'sender_email': 'zoyah768@gmail.com',
    'sender_password': 'ksha odyf dfyw eptm',
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587
}

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
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
                  job_id INTEGER NOT NULL,
                  job_title TEXT NOT NULL,
                  company TEXT NOT NULL,
                  scheduled_time TEXT NOT NULL,
                  status TEXT DEFAULT 'Scheduled',
                  notes TEXT,
                  FOREIGN KEY (candidate_id) REFERENCES candidates (id),
                  FOREIGN KEY (job_id) REFERENCES jobs (id))''')
    
    # Applications table
    c.execute('''CREATE TABLE IF NOT EXISTS applications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  candidate_id INTEGER NOT NULL,
                  job_id INTEGER NOT NULL,
                  match_score REAL NOT NULL,
                  status TEXT DEFAULT 'Applied',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (candidate_id) REFERENCES candidates (id),
                  FOREIGN KEY (job_id) REFERENCES jobs (id))''')
    
    # Jobs table (now includes company_email)
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_title TEXT NOT NULL,
                  company TEXT NOT NULL,
                  location TEXT,
                  description TEXT NOT NULL,
                  requirements TEXT NOT NULL,
                  company_email TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

def is_valid_email(email):
    """Check if email is valid"""
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))

def send_application_with_resume(candidate_email, candidate_name, resume_path, 
                                job_title, company, company_email):
    """Send application with resume to company and confirmation to candidate"""
    try:
        # Email to company
        subject_company = f"New Application for {job_title}"
        body_company = f"""Dear Hiring Team,

A new application has been received for the {job_title} position at {company}.

Candidate Details:
- Name: {candidate_name}
- Email: {candidate_email}

Please find the resume attached.

Best regards,
Recruitment Portal
"""
        
        # Create company email
        msg_company = MIMEMultipart()
        msg_company['From'] = SMTP_CONFIG['sender_email']
        msg_company['To'] = company_email
        msg_company['Subject'] = subject_company
        msg_company.attach(MIMEText(body_company, 'plain'))
        
        # Attach resume
        with open(resume_path, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', 
                            filename=f"{candidate_name}_Resume.pdf")
            msg_company.attach(attach)
        
        # Email to candidate
        subject_candidate = f"Application Confirmation: {job_title} at {company}"
        body_candidate = f"""Dear {candidate_name},

Thank you for applying to the {job_title} position at {company}. 
Your application has been successfully submitted.

We will review your qualifications and contact you if there's a match.

Best regards,
{company} Recruitment Team
"""
        
        msg_candidate = MIMEMultipart()
        msg_candidate['From'] = SMTP_CONFIG['sender_email']
        msg_candidate['To'] = candidate_email
        msg_candidate['Subject'] = subject_candidate
        msg_candidate.attach(MIMEText(body_candidate, 'plain'))
        
        # Send both emails
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_CONFIG['smtp_server'], SMTP_CONFIG['smtp_port']) as server:
            server.starttls(context=context)
            server.login(SMTP_CONFIG['sender_email'], SMTP_CONFIG['sender_password'])
            
            # Send to company
            server.sendmail(SMTP_CONFIG['sender_email'], 
                          company_email, 
                          msg_company.as_string())
            
            # Send to candidate
            server.sendmail(SMTP_CONFIG['sender_email'], 
                          candidate_email, 
                          msg_candidate.as_string())
        
        return True
    except Exception as e:
        st.error(f"Failed to send application email: {str(e)}")
        return False

init_db()

# Streamlit Page Config
st.set_page_config(page_title="Recruiter AI Assistant", page_icon="👔", layout="wide")

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
# Tab 1: AI Resume Matcher
# ---------------------------------
with tab1:
    st.title("AI-Powered Candidate Matcher")
    st.subheader("Find the best job matches for your resume")
    
    if 'step' not in st.session_state:
        st.session_state['step'] = 1
    
    # Step 1: Collect contact info
    if st.session_state['step'] == 1:
        st.subheader("Step 1: Enter your contact information")
        
        with st.form("contact_info_form"):
            candidate_name = st.text_input("Full Name*", key="name")
            candidate_email = st.text_input("Email Address*", key="email")
            candidate_phone = st.text_input("Phone Number*", key="phone")
            
            submit_info = st.form_submit_button("Continue to Resume Upload")
            
            if submit_info:
                if not candidate_name or not candidate_email or not candidate_phone:
                    st.error("Please fill in all required fields!")
                else:
                    st.session_state['candidate_name'] = candidate_name
                    st.session_state['candidate_email'] = candidate_email
                    st.session_state['candidate_phone'] = candidate_phone
                    st.session_state['step'] = 2
                    st.rerun()
    
    # Step 2: Upload resume and process
    elif st.session_state['step'] == 2:
        st.subheader("Step 2: Upload your resume")
        st.write(f"Contact info: {st.session_state['candidate_name']} | {st.session_state['candidate_email']} | {st.session_state['candidate_phone']}")
        
        uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
        
        if uploaded_file:
            with st.spinner("Analyzing resume and finding matching jobs..."):
                try:
                    # Save resume temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.read())
                        resume_path = Path(tmp_file.name)
                    
                    # Save candidate to database
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('''INSERT INTO candidates 
                                (name, email, phone, resume_path)
                                VALUES (?, ?, ?, ?)''',
                             (st.session_state['candidate_name'],
                              st.session_state['candidate_email'],
                              st.session_state['candidate_phone'],
                              str(resume_path)))
                    candidate_id = c.lastrowid
                    conn.commit()
                    conn.close()
                    
                    # Find matching jobs
                    job_finder = job_matcher.JobFinder(DB_PATH)
                    best_jobs = job_finder.find_best_jobs_from_pdf(resume_path, api_key=API_KEY)
                    
                    # Store in session state
                    st.session_state['candidate_id'] = candidate_id
                    st.session_state['best_jobs'] = best_jobs
                    st.session_state['resume_path'] = str(resume_path)
                    st.session_state['step'] = 3
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error processing resume: {str(e)}")
        
        if st.button("Go Back"):
            st.session_state['step'] = 1
            st.rerun()
    
    # Step 3: Show results and application options
    elif st.session_state['step'] == 3:
        st.subheader("Step 3: Review job matches")
        
        candidate_id = st.session_state['candidate_id']
        best_jobs = st.session_state['best_jobs']
        
        if best_jobs is not None and not best_jobs.empty:
            st.success(f"Found {len(best_jobs)} matching jobs!")
            
            for idx, row in best_jobs.iterrows():
                match_score = row['match_score']
                match_color = "green" if match_score >= 80 else "orange" if match_score >= 60 else "red"
                
                with st.container():
                    st.markdown(f"### {row['job_title']} at {row['company']}")
                    st.markdown(f"<span style='color:{match_color};font-weight:bold;'>Match Score: {match_score}%</span>", unsafe_allow_html=True)
                    
                    with st.expander("View Details"):
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
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if match_score >= 60:  # Lowered threshold for demo
                            if st.button("Apply Now", key=f"apply_{idx}"):
                                conn = sqlite3.connect(DB_PATH)
                                c = conn.cursor()
                                
                                # Get job details including company_email
                                c.execute('''SELECT id, company_email FROM jobs 
                                             WHERE job_title = ? AND company = ?''',
                                         (row['job_title'], row['company']))
                                job_data = c.fetchone()
                                
                                if job_data:
                                    job_id, company_email = job_data
                                    
                                    # Save application
                                    c.execute('''INSERT INTO applications
                                                (candidate_id, job_id, match_score)
                                                VALUES (?, ?, ?)''',
                                             (candidate_id, job_id, match_score))
                                    conn.commit()
                                    
                                    # Send emails with resume
                                    if send_application_with_resume(
                                        st.session_state['candidate_email'],
                                        st.session_state['candidate_name'],
                                        st.session_state['resume_path'],
                                        row['job_title'],
                                        row['company'],
                                        company_email
                                    ):
                                        st.success(f"✅ Application sent successfully for {row['job_title']}!")
                                    else:
                                        st.error("Failed to send application emails")
                                else:
                                    st.error("Job details not found in database")
                                conn.close()
                    
                    with col2:
                        if st.button("Schedule Interview", key=f"schedule_{idx}"):
                            st.session_state['schedule_for'] = {
                                'candidate_id': candidate_id,
                                'candidate_name': st.session_state['candidate_name'],
                                'candidate_email': st.session_state['candidate_email'],
                                'job_title': row['job_title'],
                                'company': row['company'],
                                'match_score': match_score
                            }
                            st.session_state['current_tab'] = 'tab3'
                            st.rerun()
                
                st.markdown("---")
        else:
            st.warning("No strong matches found for your resume")
        
        if st.button("Start Over"):
            if 'resume_path' in st.session_state and os.path.exists(st.session_state['resume_path']):
                os.unlink(st.session_state['resume_path'])
            
            for key in ['step', 'candidate_id', 'candidate_name', 'candidate_email', 
                       'candidate_phone', 'best_jobs', 'resume_path']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state['step'] = 1
            st.rerun()

# ---------------------------------
# Tab 2: Job Board
# ---------------------------------
with tab2:
    st.title("Job Board")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Search jobs by title, company, or keywords", "")
    with col2:  
        search_location = st.text_input("Location", "")
        
    # Add new job form
    with st.expander("➕ Add New Job Position (Admin)"):
        with st.form("job_form"):
            title = st.text_input("Job Title*")
            company = st.text_input("Company*")
            location = st.text_input("Location")
            description = st.text_area("Description*")
            requirements = st.text_area("Requirements*")
            company_email = st.text_input("Company Email*")
            
            if st.form_submit_button("Save Job"):
                if not is_valid_email(company_email):
                    st.error("Please enter a valid company email address")
                else:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute('''INSERT INTO jobs
                                (job_title, company, location, description, 
                                 requirements, company_email)
                                VALUES (?, ?, ?, ?, ?, ?)''',
                             (title, company, location, description, 
                              requirements, company_email))
                    conn.commit()
                    conn.close()
                    st.success(f"Added {title} at {company}")
    
    # View jobs
    st.subheader("Available Positions")
    try:
        conn = sqlite3.connect(DB_PATH)
        jobs_df = pd.read_sql_query('''SELECT id, job_title, company, location, 
                                      description, requirements, company_email 
                                      FROM jobs''', conn)
        conn.close()
        
        if not jobs_df.empty:
            # Filter jobs
            if search_term:
                search_term = search_term.lower()
                jobs_df = jobs_df[
                    jobs_df['job_title'].str.lower().str.contains(search_term) | 
                    jobs_df['company'].str.lower().str.contains(search_term) | 
                    jobs_df['description'].str.lower().str.contains(search_term)
                ]
            
            if search_location:
                search_location = search_location.lower()
                jobs_df = jobs_df[
                    jobs_df['location'].str.lower().str.contains(search_location)
                ]
            
            if not jobs_df.empty:
                st.write(f"Showing {len(jobs_df)} jobs")
                
                for _, row in jobs_df.iterrows():
                    with st.container():
                        st.subheader(f"{row['job_title']} at {row['company']}")
                        st.caption(f"📍 {row.get('location', 'Remote')}")
                        
                        with st.expander("View Details"):
                            st.write(row['description'])
                            st.subheader("Requirements")
                            st.write(row['requirements'])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Apply Now", key=f"apply_{row['id']}"):
                                    if 'candidate_id' in st.session_state:
                                        # Send application with resume
                                        if send_application_with_resume(
                                            st.session_state['candidate_email'],
                                            st.session_state['candidate_name'],
                                            st.session_state['resume_path'],
                                            row['job_title'],
                                            row['company'],
                                            row['company_email']
                                        ):
                                            # Save application to database
                                            conn = sqlite3.connect(DB_PATH)
                                            c = conn.cursor()
                                            c.execute('''INSERT INTO applications
                                                        (candidate_id, job_id, match_score)
                                                        VALUES (?, ?, ?)''',
                                                     (st.session_state['candidate_id'],
                                                      row['id'],
                                                      100))  # Manual application gets full score
                                            conn.commit()
                                            conn.close()
                                            st.success("Application submitted!")
                                    else:
                                        st.warning("Please upload your resume first in the AI Resume Matcher tab")
                            
                            with col2:
                                if st.button("Save Job", key=f"save_{row['id']}"):
                                    st.info("Job saved to your profile")
                        
                        st.divider()
            else:
                st.info("No jobs match your search criteria")
        else:
            st.info("No jobs available at this time")
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
        
        with st.form("interview_form"):
            interview_date = st.date_input("Date", min_value=datetime.now().date())
            interview_time = st.time_input("Time")
            interview_notes = st.text_area("Notes")
            
            if st.form_submit_button("Confirm Schedule"):
                scheduled_time = f"{interview_date} {interview_time}"
                
                # Save to database
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                
                # Get job ID
                c.execute('''SELECT id FROM jobs 
                            WHERE job_title = ? AND company = ?''',
                         (candidate['job_title'], candidate['company']))
                job_id = c.fetchone()[0]
                
                c.execute('''INSERT INTO interviews
                            (candidate_id, job_id, job_title, company, scheduled_time, notes)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                         (candidate['candidate_id'],
                          job_id,
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
        
        if st.button("Cancel"):
            del st.session_state['schedule_for']
            st.rerun()
    else:
        # View scheduled interviews
        st.subheader("Upcoming Interviews")
        conn = sqlite3.connect(DB_PATH)
        interviews = pd.read_sql_query('''SELECT i.id, c.name, i.job_title, 
                                         i.company, i.scheduled_time, i.status
                                         FROM interviews i
                                         JOIN candidates c ON i.candidate_id = c.id
                                         ORDER BY i.scheduled_time''', conn)
        conn.close()
        
        if not interviews.empty:
            for _, row in interviews.iterrows():
                with st.expander(f"{row['job_title']} with {row['name']}"):
                    st.write(f"🏢 {row['company']}")
                    st.write(f"⏰ {row['scheduled_time']}")
                    st.write(f"📌 Status: {row['status']}")
                    
                    if st.button("Reschedule", key=f"reschedule_{row['id']}"):
                        st.info("Rescheduling functionality would go here")
        else:
            st.info("No interviews scheduled yet")

# Footer
st.markdown("---")
st.caption("Recruiter AI Assistant v1.0 | Secure Hiring Platform")