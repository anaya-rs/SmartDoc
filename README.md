# SmartDoc Analyzer

Transform your documents into intelligent, searchable content with AI-powered analysis and natural language questioning capabilities.

### Features

- **AI Question Answering**: Ask natural language questions about document content
- **Batch Processing**: Upload and analyze multiple documents simultaneously
- **Modern Interface**: Beautiful, responsive design with custom color palette
- **Advanced Search**: Real-time text search with highlighting
- **Export Options**: Copy to clipboard or download extracted text
- **Session Management**: Proper file handling with cleanup capabilities

### Prerequisites

- Python 3.7 or higher
- Tesseract OCR installed on your system
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smart-ocr-analyzer.git
   cd smart-ocr-analyzer
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Tesseract OCR**

   **Windows:**
   - Download from [GitHub Tesseract releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add Tesseract to your system PATH

   **macOS:**
   ```bash
   brew install tesseract
   ```

   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   ```

4. **Verify Tesseract installation**
   ```bash
   tesseract --version
   ```

### Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5000`

3. **Upload documents**
   - Drag and drop images onto the upload area
   - Or click to browse and select files
   - Multiple files supported

4. **Extract text**
   - Click "Extract Text from All Images"
   - Wait for processing to complete

5. **Ask questions**
   - Use quick question buttons for common queries
   - Or type custom questions in natural language
   - Examples: "Who is mentioned?", "What's the amount?", "What dates are mentioned?"

6. **Manage results**
   - Copy extracted text to clipboard
   - Download as text file
   - Search within extracted content

### Project Structure

```
smart-ocr-analyzer/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html           # HTML template with embedded CSS/JS
├── uploads/                 # Temporary file storage (auto-created)
└── README.md               # This file
```

### Configuration

The application includes several configurable parameters in `app.py`:

- **Upload folder**: Change `UPLOAD_FOLDER` variable
- **File size limit**: Modify `MAX_CONTENT_LENGTH` (default: 16MB)
- **Allowed extensions**: Update `ALLOWED_EXTENSIONS` set
- **OCR configurations**: Customize in `extract_text_from_image()` function

### API Endpoints

- `GET /` - Main application interface
- `POST /upload` - Upload and process documents
- `POST /ask` - Ask questions about documents
- `POST /search` - Search within extracted text
- `POST /delete_file` - Delete specific uploaded file
- `POST /clear_session` - Clear all session data

### Dependencies

```txt
flask==2.3.3
pytesseract==0.3.10
pillow==10.0.0
opencv-python==4.8.0.74
numpy==1.24.3
werkzeug==2.3.7
```

### Technologies Used

- **Backend**: Flask, Python 3.7+
- **OCR Engine**: Tesseract OCR with OpenCV preprocessing
- **Image Processing**: PIL, OpenCV, NumPy
- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5
- **File Handling**: Werkzeug for secure file uploads
