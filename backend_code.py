import os
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

# Function to extract text from different resume formats
def extract_text(file_path):
    if file_path.endswith('.docx'):
        return docx2txt.process(file_path)
    elif file_path.endswith('.pdf'):
        with open(file_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfFileReader(pdf_file)
            text = ''
            for page in range(reader.numPages):
                text += reader.getPage(page).extract_text()
            return text
    else:
        return textract.process(file_path).decode('utf-8')

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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        job_description = request.form['job_description']
        files = request.files.getlist('resumes')
        
        results = []
        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                resume_text = extract_text(file_path)
                match_percentage = match_resume_with_job_description(job_description, resume_text)
                
                results.append({'filename': filename, 'match_percentage': match_percentage})

        return render_template('results.html', results=results)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)

