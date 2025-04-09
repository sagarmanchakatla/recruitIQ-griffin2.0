# streamlit_app.py
import sys
import os
import random
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Now you can import
import job_matcher

import streamlit as st
import pandas as pd
import tempfile

# Constants
DB_PATH = "../job_analysis.db"
API_KEY = "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"

# Placeholder Images (random pics)
PLACEHOLDER_IMAGES = [
    "https://source.unsplash.com/400x300/?career",
    "https://source.unsplash.com/400x300/?office",
    "https://source.unsplash.com/400x300/?work",
    "https://source.unsplash.com/400x300/?job",
    "https://source.unsplash.com/400x300/?technology",
    "https://source.unsplash.com/400x300/?startup"
]

# Streamlit Page Config
st.set_page_config(page_title="Resume Matcher", page_icon="🧠", layout="wide")

# Tabs
tab1, tab2 = st.tabs(["🎯 Resume Matcher", "📋 All Jobs Board"])

# ---------------------------------
# Tab 1: Resume Matcher
# ---------------------------------
with tab1:
    st.title("🧠 Resume Matcher using Gemini AI")
    st.subheader("Upload your Resume and get the Best Job Matches!")

    # Upload Resume
    uploaded_file = st.file_uploader("Upload your resume (PDF format)", type=["pdf"])

    if uploaded_file:
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.read())
            resume_path = Path(tmp_file.name)

        # Initialize Job Finder
        job_finder = job_matcher.JobFinder(DB_PATH)

        # Analyze Resume and Find Best Jobs
        with st.spinner("Processing your resume... This may take a few seconds..."):
            try:
                best_jobs = job_finder.find_best_jobs_from_pdf(resume_path, api_key=API_KEY)

                if best_jobs is not None and not best_jobs.empty:
                    st.success("✅ Here are your best matches!")
                    
                    for idx, row in best_jobs.iterrows():
                        with st.expander(f"🎯 {row['job_title']} at {row['company']} - Score: {row['match_score']}%"):
                            st.markdown(f"**Recommendation:** {row['recommendation']}")
                            st.markdown("**Strengths:**")
                            for strength in row['strengths']:
                                st.markdown(f"- ✅ {strength}")
                            st.markdown("**Weaknesses:**")
                            for weakness in row['weaknesses']:
                                st.markdown(f"- ⚠️ {weakness}")
                else:
                    st.warning("No good matches found. Try another resume.")

            except Exception as e:
                st.error(f"Something went wrong: {e}")

            finally:
                job_finder.close()

        # Clean up temporary file
        os.unlink(resume_path)

# ---------------------------------
# Tab 2: All Jobs Board
# ---------------------------------
with tab2:
    st.title("📋 All Available Jobs")
    st.subheader("Explore all the open job opportunities!")

    # Initialize Job Finder
    job_finder = job_matcher.JobFinder(DB_PATH)

    try:
        all_jobs = job_finder.get_all_jobs()

        if all_jobs is not None and not all_jobs.empty:
            for idx, row in all_jobs.iterrows():
                with st.container():
                    cols = st.columns([1, 3])
                    
                    # Random image
                    with cols[0]:
                        img_url = random.choice(PLACEHOLDER_IMAGES)
                        st.image(img_url, use_container_width =True)
                    
                    # Job details
                    with cols[1]:
                        st.subheader(f"{row['job_title']} at {row['company']}")
                        st.markdown(f"📍 **Location:** {row.get('location', 'Unknown')}")
                        st.markdown(f"📝 **Description:** {row.get('job_summary', 'No description available.')}")
                        st.markdown(f"📅 **Posted On:** {row.get('posted_date', 'N/A')}")
                        st.divider()

        else:
            st.info("No jobs found in the database.")

    except Exception as e:
        st.error(f"Could not fetch jobs: {e}")

    finally:
        job_finder.close()

# Footer
st.markdown("---")
st.caption("Built with ❤️ using Streamlit, Gemini, and Llama AI")
