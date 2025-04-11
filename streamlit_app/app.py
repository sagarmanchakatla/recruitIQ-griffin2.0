import re
from email.mime.application import MIMEApplication
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
# Update the init_db function to include a jobs table
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
    
    # Applications table
    c.execute('''CREATE TABLE IF NOT EXISTS applications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  candidate_id INTEGER NOT NULL,
                  job_id TEXT NOT NULL,
                  job_title TEXT NOT NULL,
                  company TEXT NOT NULL,
                  match_score REAL NOT NULL,
                  status TEXT DEFAULT 'Applied',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (candidate_id) REFERENCES candidates (id))''')
    
    # Jobs table (new)
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_title TEXT NOT NULL,
                  company TEXT NOT NULL,
                  location TEXT,
                  description TEXT NOT NULL,
                  requirements TEXT NOT NULL,
                  salary TEXT,
                  job_type TEXT,
                  recruiter_email TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

# Add this email sending function (put it with other email functions)
def send_application_with_resume(candidate_email, candidate_name, resume_path, 
                                job_title, company, company_email=None):
    """Send application with resume to company and confirmation to candidate"""
    try:
        # Email to company (only if company_email is provided and valid)
        if company_email and isinstance(company_email, str) and '@' in company_email:
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
        
        # Email to candidate (always send)
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
        
        # Send emails
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_CONFIG['smtp_server'], SMTP_CONFIG['smtp_port']) as server:
            server.starttls(context=context)
            server.login(SMTP_CONFIG['sender_email'], SMTP_CONFIG['sender_password'])
            
            # Send to company if email was provided
            if 'msg_company' in locals():
                server.sendmail(SMTP_CONFIG['sender_email'], 
                              company_email, 
                              msg_company.as_string())
            
            # Always send to candidate
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

def send_application_email(candidate_email, candidate_name, job_title, company, recruiter_email=None):
    """Send application confirmation email to candidate and notification to company"""
    # Email to candidate
    subject_candidate = f"Application Confirmation: {job_title} at {company}"
    body_candidate = f"""Dear {candidate_name},

Thank you for applying to the {job_title} position at {company}. Your application has been successfully submitted.

We will review your qualifications and get back to you soon regarding next steps.

Best regards,
Recruitment Team
"""
    
    try:
        # Send confirmation to candidate
        msg_candidate = MIMEMultipart()
        msg_candidate['From'] = SMTP_CONFIG['sender_email']
        msg_candidate['To'] = candidate_email
        msg_candidate['Subject'] = subject_candidate
        msg_candidate.attach(MIMEText(body_candidate, 'plain'))
        
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_CONFIG['smtp_server'], SMTP_CONFIG['smtp_port']) as server:
            server.starttls(context=context)
            server.login(SMTP_CONFIG['sender_email'], SMTP_CONFIG['sender_password'])
            server.sendmail(SMTP_CONFIG['sender_email'], candidate_email, msg_candidate.as_string())
        
        # Send notification to company if recruiter email is provided
        if recruiter_email:
            subject_company = f"New Application: {job_title}"
            body_company = f"""Hello,

A new application has been received for the {job_title} position.

Candidate: {candidate_name}
Email: {candidate_email}

The application has been recorded in the system.

Automated Recruiting System
"""
            
            msg_company = MIMEMultipart()
            msg_company['From'] = SMTP_CONFIG['sender_email']
            msg_company['To'] = recruiter_email
            msg_company['Subject'] = subject_company
            msg_company.attach(MIMEText(body_company, 'plain'))
            
            server.sendmail(SMTP_CONFIG['sender_email'], recruiter_email, msg_company.as_string())
        
        return True
    except Exception as e:
        st.error(f"Failed to send application email: {str(e)}")
        return False

# Tabs
tab1, tab2, tab3 = st.tabs(["🧠 AI Resume Matcher", "📋 Job Board", "📅 Interview Scheduler"])

# ---------------------------------
# Tab 1: AI Resume Matcher (Recruiter View)
# ---------------------------------
with tab1:
    st.title("AI-Powered Candidate Matcher")
    st.subheader("Find the best job matches for your resume")
    
    # Initialize session state for multi-step process
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
                    # Save contact info in session state
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
                    
                    # Extract candidate info from session state
                    candidate_name = st.session_state['candidate_name']
                    candidate_email = st.session_state['candidate_email']
                    candidate_phone = st.session_state['candidate_phone']
                    
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
            
            # Display matches
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
                    
                    # Actions based on match score
                    col1, col2 = st.columns(2)
                    with col1:
                        if match_score >= 80:
                            if st.button("Apply Now", key=f"apply_{idx}"):
                                # Save application to database
                                conn = sqlite3.connect(RECRUITER_DB)
                                c = conn.cursor()
                                
                                # Get company email from jobs table
                                c.execute('''SELECT company_email FROM jobs 
                                            WHERE job_title = ? AND company = ?''',
                                        (row['job_title'], row['company']))
                                job_data = c.fetchone()
                                company_email = job_data[0] if job_data else None
                                
                                # Ensure company_email is a string
                                if company_email is not None:
                                    company_email = str(company_email)
                                
                                c.execute('''INSERT INTO applications
                                            (candidate_id, job_id, job_title, company, match_score)
                                            VALUES (?, ?, ?, ?, ?)''',
                                        (candidate_id,
                                        row.get('job_id', ''),
                                        row['job_title'],
                                        row['company'],
                                        match_score))
                                conn.commit()
                                conn.close()
                                
                                # Send confirmation emails
                                if send_application_with_resume(
                                    st.session_state['candidate_email'], 
                                    st.session_state['candidate_name'],
                                    st.session_state['resume_path'],
                                    row['job_title'],
                                    row['company'],
                                    company_email  # Pass the fetched company email
                                ):
                                    st.success(f"✅ Application sent successfully for {row['job_title']}!")
                    
                    with col2:
                        if st.button("Schedule Interview", key=f"schedule_{idx}"):
                            st.session_state['schedule_for'] = {
                                'candidate_id': candidate_id,
                                'candidate_name': st.session_state['candidate_name'],
                                'candidate_email': st.session_state['candidate_email'],
                                'job_id': row.get('job_id', ''),
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
            # Clean up
            if 'resume_path' in st.session_state and os.path.exists(st.session_state['resume_path']):
                os.unlink(st.session_state['resume_path'])
            
            # Reset session state
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
    
    # Search functionality
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input("Search jobs by title, company, or keywords", "")
    with col2:  
        search_location = st.text_input("Location", "")
        
    # Add new job form (for admin/recruiter)
    # In your "Add New Job Position" form in Tab 2
    with st.expander("➕ Add New Job Position (Admin)"):
        with st.form("job_form"):
            title = st.text_input("Job Title*")
            company = st.text_input("Company*")
            location = st.text_input("Location")
            description = st.text_area("Description*")
            requirements = st.text_area("Requirements*")
            company_email = st.text_input("Company Email*")
            
            if st.form_submit_button("Save Job"):
                # Validate email format
                if not re.match(r"[^@]+@[^@]+\.[^@]+", company_email):
                    st.error("Please enter a valid company email address")
                else:
                    conn = sqlite3.connect(RECRUITER_DB)
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
        job_finder = job_matcher.JobFinder(DB_PATH)
        all_jobs = job_finder.get_all_jobs()
        
        if all_jobs is not None and not all_jobs.empty:
            # Filter by search terms if provided
            if search_term:
                search_term = search_term.lower()
                filtered_jobs = all_jobs[
                    all_jobs['job_title'].str.lower().str.contains(search_term) | 
                    all_jobs['company'].str.lower().str.contains(search_term) | 
                    all_jobs['job_summary'].str.lower().str.contains(search_term)
                ]
            else:
                filtered_jobs = all_jobs
            
            # Filter by location if provided
            if search_location and 'location' in filtered_jobs.columns:
                search_location = search_location.lower()
                filtered_jobs = filtered_jobs[
                    filtered_jobs['location'].str.lower().str.contains(search_location)
                ]
            
            if not filtered_jobs.empty:
                st.write(f"Showing {len(filtered_jobs)} jobs")
                
                for idx, row in filtered_jobs.iterrows():
                    with st.container():
                        st.subheader(f"{row['job_title']} at {row['company']}")
                        st.caption(f"📍 {row.get('location', 'Remote')} | 📅 Posted: {row.get('posted_date', 'N/A')}")
                        
                        with st.expander("View Details"):
                            st.write(row.get('job_summary', 'No description available.'))
                            
                            # Additional job details
                            if 'requirements' in row:
                                st.subheader("Requirements")
                                st.write(row['requirements'])
                            
                            if 'salary_range' in row:
                                st.subheader("Salary Range")
                                st.write(row['salary_range'])
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                # This would need user authentication in a real app
                                if st.button("Apply Now", key=f"apply_direct_{idx}"):
                                    if 'candidate_id' in st.session_state:
                                        st.success("Application submitted!")
                                    else:
                                        st.warning("Please go to AI Resume Matcher tab to upload your resume first")
                            
                            with col2:
                                if st.button("Save Job", key=f"save_{idx}"):
                                    st.info("Job saved to your profile")
                        
                        st.divider()
            else:
                st.info("No jobs match your search criteria")
        else:
            st.info("No jobs available at this time")
            
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
        
        if st.button("Cancel"):
            del st.session_state['schedule_for']
            st.rerun()
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