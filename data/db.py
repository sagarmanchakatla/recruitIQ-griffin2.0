import sqlite3
import csv
from typing import List

def create_database(db_name: str = "job_listings.db") -> sqlite3.Connection:
    """Creates an SQLite database with a table for job listings."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_title TEXT,
        category TEXT,
        experience_level TEXT,
        key_responsibilities TEXT,
        technical_requirements TEXT,
        preferred_qualifications TEXT,
        soft_skills TEXT,
        company_culture TEXT,
        tech_stack TEXT,
        salary_range TEXT,
        location TEXT,
        benefits TEXT,
        application_process TEXT
    )
    """)
    conn.commit()
    return conn

def insert_job(conn: sqlite3.Connection, job_data: List[str]) -> None:
    """Inserts a single job listing into the database."""
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO jobs (
        job_title, category, experience_level, key_responsibilities,
        technical_requirements, preferred_qualifications, soft_skills,
        company_culture, tech_stack, salary_range, location, benefits,
        application_process
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, job_data)
    conn.commit()

def import_from_csv(conn: sqlite3.Connection, csv_file: str) -> None:
    """Imports job listings from a CSV file into the database."""
    with open(csv_file, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            job_data = [
                row['Job Title'],
                row['Category'],
                row['Experience Level'],
                row['Key Responsibilities'],
                row['Technical Requirements'],
                row['Preferred Qualifications'],
                row['Soft Skills'],
                row['Company Culture'],
                row['Tech Stack'],
                row['Salary Range'],
                row['Location'],
                row['Benefits'],
                row['Application Process']
            ]
            insert_job(conn, job_data)
    print(f"Imported data from {csv_file}")

if __name__ == "__main__":
    # Initialize the database
    conn = create_database()

    # Example CSV file (replace with your actual file path)
    csv_file = "data.csv"  # Your CSV with the specified fields

    # Import data from CSV
    import_from_csv(conn, csv_file)

    # Verify data insertion
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jobs")
    print(f"Total jobs in database: {cursor.fetchone()[0]}")

    # Close connection
    conn.close()