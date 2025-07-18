from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
import os
import pytesseract
from PIL import Image
import cv2
import numpy as np
from datetime import datetime
import secrets
import re
import shutil

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image(image_path):
    """Simple, reliable image preprocessing"""
    image = cv2.imread(image_path)
    if image is None:
        return None
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Resize if too small
    height, width = gray.shape
    if height < 300 or width < 300:
        scale = max(300/height, 300/width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    
    # Basic noise reduction
    denoised = cv2.medianBlur(gray, 3)
    
    # Simple thresholding
    _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def extract_text_from_image(image_path):
    """More robust OCR extraction with fallback options"""
    try:
        # Method 1: Direct OCR without preprocessing
        try:
            text = pytesseract.image_to_string(image_path, config='--oem 3 --psm 6')
            if text.strip() and len(text.strip()) > 10:
                return text.strip()
        except:
            pass
        
        # Method 2: Basic preprocessing
        image = cv2.imread(image_path)
        if image is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Simple resize if needed
            height, width = gray.shape
            if height < 600:
                scale = 600 / height
                new_width = int(width * scale)
                new_height = int(height * scale)
                gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Try different OCR modes
            configs = [
                '--oem 3 --psm 6',
                '--oem 3 --psm 4',
                '--oem 3 --psm 8',
                '--oem 3 --psm 7'
            ]
            
            for config in configs:
                try:
                    text = pytesseract.image_to_string(gray, config=config)
                    if text.strip() and len(text.strip()) > 10:
                        return text.strip()
                except:
                    continue
        
        return None
        
    except Exception as e:
        print(f"OCR Error: {str(e)}")
        return None

def analyze_document_content(question, context):
    """Enhanced AI analysis with better pattern matching and context understanding"""
    question_lower = question.lower()
    context_lower = context.lower()
    
    # Enhanced patterns for different document types
    patterns = {
        'who': {
            'keywords': ['who', 'name', 'person', 'individual', 'student', 'customer', 'user'],
            'patterns': [
                r'name\s*:?\s*([A-Za-z\s]+)',
                r'student\s*name\s*:?\s*([A-Za-z\s]+)',
                r'customer\s*name\s*:?\s*([A-Za-z\s]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'by\s*:?\s*([A-Za-z\s]+)',
                r'from\s*:?\s*([A-Za-z\s]+)',
            ]
        },
        'what': {
            'keywords': ['what', 'which', 'type', 'category', 'purpose', 'reason', 'for'],
            'patterns': [
                r'category\s*:?\s*([^:\n]+)',
                r'purpose\s*:?\s*([^:\n]+)',
                r'payment\s*purpose\s*:?\s*([^:\n]+)',
                r'reason\s*:?\s*([^:\n]+)',
                r'type\s*:?\s*([^:\n]+)',
                r'description\s*:?\s*([^:\n]+)',
            ]
        },
        'amount': {
            'keywords': ['amount', 'money', 'cost', 'price', 'fee', 'charge', 'payment'],
            'patterns': [
                r'amount\s*:?\s*[₹$]?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'fee\s*:?\s*[₹$]?(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'charge\s*:?\s*[₹$]?(\d+(?:,\d{3})*(?:\.\d{2})?)',
            ]
        },
        'reference': {
            'keywords': ['reference', 'number', 'id', 'transaction', 'receipt'],
            'patterns': [
                r'reference\s*number\s*:?\s*([A-Z0-9]+)',
                r'transaction\s*id\s*:?\s*([A-Z0-9]+)',
                r'receipt\s*number\s*:?\s*([A-Z0-9]+)',
                r'student\s*id\s*:?\s*([A-Z0-9]+)',
                r'id\s*:?\s*([A-Z0-9]+)',
            ]
        },
        'when': {
            'keywords': ['when', 'date', 'time', 'day'],
            'patterns': [
                r'date\s*:?\s*([^:\n]+)',
                r'time\s*:?\s*([^:\n]+)',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            ]
        }
    }
    
    # Determine question type with better matching
    question_type = None
    for qtype, data in patterns.items():
        if any(keyword in question_lower for keyword in data['keywords']):
            question_type = qtype
            break
    
    # Special handling for amount/money questions
    if any(word in question_lower for word in ['much', 'amount', 'money', 'cost', 'fee', 'price']):
        question_type = 'amount'
    
    # Special handling for reference/ID questions
    if any(word in question_lower for word in ['reference', 'id', 'number', 'transaction']):
        question_type = 'reference'
    
    # Extract relevant information
    relevant_info = []
    
    if question_type and question_type in patterns:
        for pattern in patterns[question_type]['patterns']:
            matches = re.findall(pattern, context, re.IGNORECASE)
            if matches:
                # Clean up matches
                cleaned_matches = []
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match else ''
                    cleaned_match = match.strip()
                    if cleaned_match and len(cleaned_match) > 1:
                        cleaned_matches.append(cleaned_match)
                relevant_info.extend(cleaned_matches)
    
    # Generate specific answers based on question type
    if relevant_info:
        unique_info = list(dict.fromkeys(relevant_info))  # Remove duplicates while preserving order
        
        if question_type == 'who':
            return f"Based on the document, the person mentioned is: {unique_info[0]}"
        elif question_type == 'what':
            return f"This document is about: {unique_info[0]}"
        elif question_type == 'amount':
            amounts = [info for info in unique_info if info.replace(',', '').replace('.', '').isdigit()]
            if amounts:
                return f"The amount mentioned is: ₹{amounts[0]}"
            else:
                return f"The amounts mentioned are: {', '.join(unique_info[:3])}"
        elif question_type == 'reference':
            return f"The reference/ID numbers are: {', '.join(unique_info[:3])}"
        elif question_type == 'when':
            return f"The date/time mentioned is: {unique_info[0]}"
    
    # Enhanced fallback with better sentence matching
    sentences = [s.strip() for s in context.split('\n') if s.strip()]
    relevant_sentences = []
    
    # Look for lines that contain question keywords
    question_words = [word for word in question_lower.split() if len(word) > 2]
    for sentence in sentences:
        if any(word in sentence.lower() for word in question_words):
            relevant_sentences.append(sentence)
    
    if relevant_sentences:
        return f"Based on the document: {'. '.join(relevant_sentences[:2])}"
    
    # Final fallback - return document summary
    important_lines = []
    for line in sentences:
        if ':' in line and any(keyword in line.lower() for keyword in ['name', 'amount', 'purpose', 'category', 'reference']):
            important_lines.append(line)
    
    if important_lines:
        return f"Here's what I found in the document: {'. '.join(important_lines[:3])}"
    
    return "I found information in the document, but I'm not sure how to answer your specific question. Could you try rephrasing it?"

@app.route('/')
def index():
    session['extracted_texts'] = []
    session['uploaded_files'] = []
    session['document_info'] = {}
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Clear previous session data when new files are uploaded
    session.clear()
    
    if 'files' not in request.files:
        return jsonify({'error': 'No files selected'}), 400
    
    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400
    
    results = []
    extracted_texts = []
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            
            file.save(filepath)
            
            try:
                extracted_text = extract_text_from_image(filepath)
                
                if extracted_text:
                    results.append({
                        'filename': filename,
                        'filepath': filepath,
                        'text': extracted_text,
                        'word_count': len(extracted_text.split()),
                        'char_count': len(extracted_text)
                    })
                    
                    extracted_texts.append(extracted_text)
                    uploaded_files.append({
                        'filename': filename,
                        'filepath': filepath,
                        'unique_filename': unique_filename
                    })
                else:
                    return jsonify({'error': f'No text could be extracted from {filename}'}), 400
                    
            except Exception as e:
                return jsonify({'error': f'OCR processing failed for {filename}: {str(e)}'}), 500
        else:
            return jsonify({'error': f'Invalid file type: {file.filename}'}), 400
    
    # Update session with new data
    session['extracted_texts'] = extracted_texts
    session['uploaded_files'] = uploaded_files
    
    return jsonify({
        'success': True,
        'results': results,
        'total_files': len(results)
    })

@app.route('/clear_session', methods=['POST'])
def clear_session():
    """Clear all session data"""
    uploaded_files = session.get('uploaded_files', [])
    
    # Delete physical files
    for file_info in uploaded_files:
        if os.path.exists(file_info['filepath']):
            os.remove(file_info['filepath'])
    
    # Clear session completely
    session.clear()
    
    return jsonify({'success': True})

@app.route('/delete_file', methods=['POST'])
def delete_file():
    data = request.get_json()
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'error': 'No filename provided'}), 400
    
    uploaded_files = session.get('uploaded_files', [])
    extracted_texts = session.get('extracted_texts', [])
    
    for i, file_info in enumerate(uploaded_files):
        if file_info['filename'] == filename:
            if os.path.exists(file_info['filepath']):
                os.remove(file_info['filepath'])
            
            uploaded_files.pop(i)
            if i < len(extracted_texts):
                extracted_texts.pop(i)
            break
    
    session['uploaded_files'] = uploaded_files
    session['extracted_texts'] = extracted_texts
    
    return jsonify({'success': True})

@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    question = data.get('question', '').strip()
    
    if not question:
        return jsonify({'error': 'Please enter a question'}), 400
    
    extracted_texts = session.get('extracted_texts', [])
    if not extracted_texts:
        return jsonify({'error': 'Please upload and process documents first'}), 400
    
    try:
        combined_text = ' '.join(extracted_texts)
        answer = analyze_document_content(question, combined_text)
        return jsonify({
            'success': True,
            'answer': answer,
            'question': question
        })
    except Exception as e:
        return jsonify({'error': f'Error analyzing document: {str(e)}'}), 500

@app.route('/search', methods=['POST'])
def search_text():
    data = request.get_json()
    search_term = data.get('search_term', '').strip()
    
    if not search_term:
        return jsonify({'matches': [], 'count': 0})
    
    extracted_texts = session.get('extracted_texts', [])
    if not extracted_texts:
        return jsonify({'matches': [], 'count': 0})
    
    combined_text = ' '.join(extracted_texts)
    matches = []
    for match in re.finditer(re.escape(search_term), combined_text, re.IGNORECASE):
        matches.append({
            'start': match.start(),
            'end': match.end(),
            'text': match.group()
        })
    
    return jsonify({'matches': matches, 'count': len(matches)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
