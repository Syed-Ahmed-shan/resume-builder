import os
import zipfile
from flask import Flask, jsonify, render_template, request, make_response, send_file
from xhtml2pdf import pisa
from io import BytesIO
import requests 
import json

app = Flask(__name__)

# ✅ Upload folder config
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ✅ Home route
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/resume-form')
def resume_form():
    return render_template('resume_form.html')

@app.route('/portfolio-form')
def portfolio_form():
    return render_template('portfolio_form.html')

# ✅ Resume generation
@app.route('/generate-resume', methods=['POST'])
def generate_resume():
    data = request.form
    template = data['template']
    return render_template(
        f"{template}.html",
        name=data['name'],
        phone=data['phone'],
        email=data['email'],
        linkedin=data['linkedin'],
        github=data['github'],
        summary=data['summary'],
        school=data['school'],
        inter=data['inter'],
        degree=data['degree'],
        prog_skills=data['prog_skills'],
        dbms_os=data['dbms_os'],
        os=data['os'],
        tools=data['tools'],
        projects=data['projects'],
        certifications=data['certifications']
    )

# ✅ Portfolio generation
@app.route('/generate-portfolio', methods=['POST'])
def generate_portfolio():
    data = request.form
    profile_file = request.files.get('profile')
    template = data.get('template', 'portfolio1')

    if profile_file and profile_file.filename:
        profile_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_file.filename)
        profile_file.save(profile_path)
        profile_url = f'/static/uploads/{profile_file.filename}'
    else:
        profile_url = '/static/default.jpg'

    return render_template(
        f"{template}.html",
        name=data.get('name', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        linkedin=data.get('linkedin', ''),
        github=data.get('github', ''),
        summary=data.get('summary', ''),
        prog_skills=data.get('prog_skills', ''),
        dbms_os=data.get('dbms_os', ''),
        os=data.get('os', ''),
        tools=data.get('tools', ''),
        projects=data.get('projects', ''),
        certifications=data.get('certifications', ''),
        profile=profile_url
    )

# ✅ Resume download as PDF
@app.route('/download-resume', methods=['POST'])
def download_resume():
    data = request.form
    template_name = data.get('theme', 'resume1')

    if not template_name.endswith('.html'):
        template_name += '.html'

    try:
        html = render_template(template_name, **data)
    except Exception as e:
        return f"\u274c Template error: {e}", 500

    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf)

    if pisa_status.err:
        return "\u274c Error creating PDF", 500

    pdf.seek(0)
    response = make_response(pdf.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={template_name.split('.')[0]}.pdf'
    return response

# ✅ Portfolio PDF
@app.route('/download-portfolio', methods=['POST'])
def download_portfolio():
    data = request.form
    template = data.get('theme', 'portfolio3d')

    if not template.endswith('.html'):
        template += '.html'

    html = render_template(template, **data, profile="/static/uploads/default.jpg")

    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf)

    if pisa_status.err:
        return "Error generating portfolio PDF", 500

    pdf.seek(0)
    response = make_response(pdf.read())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={template.split('.')[0]}.pdf'
    return response

# ✅ Portfolio ZIP
@app.route('/download-portfolio-code', methods=['POST'])
def download_portfolio_code():
    data = request.form.to_dict()
    template = data.get("theme", "space-portfolio")

    if not template.endswith('.html'):
        template += ".html"

    html = render_template(template, **data, profile='/static/uploads/default.jpg')

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        zip_file.writestr("index.html", html)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name='portfolio_code.zip'
    )



@app.route('/ask-ai', methods=['POST'])
def ask_ai():
    try:
        data = request.get_json()
        question = data.get('question', 'Write a professional resume summary')

        response = requests.post(
            'http://localhost:11434/api/generate',
            json={"model": "gemma3", "prompt": question},
            timeout=60
        )

        if response.status_code == 200:
            # Handle streaming line-by-line response
            lines = response.text.strip().split('\n')
            full_response = ''
            for line in lines:
                try:
                    part = json.loads(line)
                    full_response += part.get('response', '')
                except:
                    continue
            return jsonify({"answer": full_response})
        else:
            return jsonify({"error": "AI Error", "details": response.text}), 500

    except Exception as e:
        return jsonify({"error": "Exception", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
