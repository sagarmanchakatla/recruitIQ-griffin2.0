import os
import sys
import argparse
from pathlib import Path
import PyPDF2
from groq import Groq

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    text = ""
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        sys.exit(1)
    return text

def extract_keywords(resume_text, api_key, model="llama3-70b-8192"):
    """Use Groq and Llama model to extract keywords from resume text."""
    client = Groq(api_key=api_key)
    
    # Create a prompt for keyword extraction
    prompt = f"""
    Below is the text extracted from a resume. Please analyze it and extract the key skills, 
    technologies, qualifications, and important keywords that would be relevant for job matching.
    Return the result as a JSON object with these categories:
    - Technical Skills
    - Soft Skills
    - Tools/Software
    - Industry Knowledge
    - Certifications
    - Education

    Resume text:
    {resume_text}
    """
    
    # Call the Groq API with the Llama model
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional resume analyzer that extracts relevant keywords."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Extract keywords from a resume PDF using Groq and Llama model")
    # parser.add_argument("--api-key", help="Groq API key (alternatively, set GROQ_API_KEY environment variable)")
    parser.add_argument("--model", default="llama3-70b-8192", help="Llama model to use (default: llama3-70b-8192)")
    parser.add_argument("--output", help="Output JSON file path (optional)")
    
    args = parser.parse_args()
    
    # Set the path to resume.pdf in the same directory as the script
    current_dir = Path(__file__).parent
    pdf_path = current_dir / "data/resume.pdf"

    if not pdf_path.exists() or not pdf_path.is_file():
        print(f"Error: PDF file not found at {pdf_path}")
        sys.exit(1)
    
    # Get API key from args or environment
    api_key = "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"
    if not api_key:
        print("Error: Groq API key is required. Provide it using --api-key argument or set GROQ_API_KEY environment variable.")
        sys.exit(1)
    
    # Extract text from the PDF
    print(f"Extracting text from {pdf_path}...")
    resume_text = extract_text_from_pdf(pdf_path)
    
    # Extract keywords using Groq and Llama
    print(f"Analyzing resume with {args.model}...")
    keywords_output = extract_keywords(resume_text, api_key, args.model)
    
    if keywords_output:
        # If output file is specified, write to file
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    f.write(keywords_output)
                print(f"Keywords saved to {args.output}")
            except Exception as e:
                print(f"Error writing to output file: {e}")
        else:
            # Otherwise print to console
            print("\nExtracted Keywords:")
            print(keywords_output)
    else:
        print("Failed to extract keywords.")

# if __name__ == "__main__":
#     main()
