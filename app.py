import os
import uuid
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
from azure.ai.openai import OpenAIClient
from azure.core.credentials import AzureKeyCredential
import docx2txt
import PyPDF2
import textract

app = Flask(__name__)

# Azure OpenAI credentials (replace with your actual keys)
api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
client = OpenAIClient(endpoint=endpoint, credential=AzureKeyCredential(api_key))

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Data structure to hold candidate information and test links
candidates = {}

# Function to extract text from different resume formats
def extract_text(file_path):
    try:
        if file_path.endswith('.docx'):
            return docx2txt.process(file_path)
        elif file_path.endswith('.pdf'):
            text = ''
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfFileReader(pdf_file)
                for page in range(reader.numPages):
                    text += reader.getPage(page).extract_text()
            return text
        else:
            return textract.process(file_path).decode('utf-8')
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return ""

# Function to match resume with job description using Azure OpenAI
def match_resume_with_job_description(job_description, resume_text):
    prompt = f"""
    Match the following resume with the job description considering skills and work experience, and provide a match percentage:
    
    Job Description:
    {job_description}
    
    Resume:
    {resume_text}
    
    Please provide a detailed analysis and a match percentage.
    """
    response = client.completions.create(
        model="text-davinci-002",
        prompt=prompt,
        max_tokens=100
    )
    return response.choices[0].text.strip()

# Function to generate test questions for a candidate
def generate_test_questions(candidate_name, job_description, resume_text):
    prompt = f"""
    Based on the following resume and job description, create 10 subjective questions to assess the candidate's skills and work experience.
    
    Job Description:
    {job_description}
    
    Resume:
    {resume_text}
    
    Provide 10 questions:
    """
    response = client.completions.create(
        model="text-davinci-002",
        prompt=prompt,
        max_tokens=500
    )
    questions = response.choices[0].text.strip().split('\n')
    return questions

# Function to generate test link
def generate_test_link(candidate_name):
    unique_id = uuid.uuid4().hex
    return f"/test/{unique_id}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        job_description = request.form['job_description']
        resumes = request.files.getlist('resumes')

        results = []
        for file in resumes:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                resume_text = extract_text(file_path)
                match_percentage = match_resume_with_job_description(job_description, resume_text)
                
                results.append({'filename': filename, 'match_percentage': match_percentage})
        
        # Filter candidates with match percentage greater than 60%
        high_match_candidates = [result for result in results if float(result['match_percentage'].strip('%')) > 60]
        
        for candidate in high_match_candidates:
            candidate_name = candidate['filename']
            resume_text = extract_text(os.path.join(app.config['UPLOAD_FOLDER'], candidate_name))
            questions = generate_test_questions(candidate_name, job_description, resume_text)
            test_link = generate_test_link(candidate_name)
            candidates[candidate_name] = {'match_percentage': candidate['match_percentage'], 'test_link': test_link, 'questions': questions, 'status': 'Pending'}

        return render_template('results.html', results=results, candidates=candidates)

    return render_template('index.html')

@app.route('/test/<test_id>', methods=['GET', 'POST'])
def test(test_id):
    candidate_name = next((name for name, details in candidates.items() if details['test_link'].endswith(test_id)), None)
    if not candidate_name:
        return "Test not found", 404
    
    candidate_info = candidates[candidate_name]
    questions = candidate_info['questions']

    if request.method == 'POST':
        answers = {f"question_{i+1}": request.form.get(f"question_{i+1}") for i in range(10)}
        candidate_info['answers'] = answers
        candidate_info['status'] = 'Submitted'
        # Here you would add logic to validate answers for plagiarism and AI-generated content
        candidate_info['plagiarism_check_result'] = "No plagiarism detected"  # Placeholder for plagiarism result
        candidate_info['ai_generated_check_result'] = "No AI-generated content detected"  # Placeholder for AI-generated check result
        return redirect(url_for('dashboard'))

    return render_template('test.html', test_id=test_id, questions=questions)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', candidates=candidates)

if __name__ == '__main__':
    app.run(debug=True)