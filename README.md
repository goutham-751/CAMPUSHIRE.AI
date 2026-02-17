# CampusHire.AI

AI-powered campus hiring platform with resume parsing, ATS scoring, interview question generation, and mock interview sessions.

## Features

- 📄 **Resume Parsing**: Extract structured data from PDF, DOCX, and TXT resumes
- 📊 **ATS Scoring**: Calculate ATS compatibility scores against job descriptions
- 💬 **Interview Questions**: Generate tailored interview questions based on resume and job description
- 🎤 **Mock Interviews**: Practice with AI-powered interview sessions and answer evaluation
- 🔊 **Voice Services**: Text-to-speech and speech-to-text capabilities

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- npm or yarn
- Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Quick Start

### Backend Setup

1. **Run the setup script:**
   ```bash
   # On Linux/Mac:
   chmod +x setup_backend.sh
   ./setup_backend.sh
   
   # On Windows:
   setup_backend.bat
   ```

2. **Create `.env` file in project root:**
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   DEBUG=True
   ```

3. **Start the backend server:**
   ```bash
   cd backend
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   uvicorn main:app --reload
   ```

The backend will be available at `http://127.0.0.1:8000`

### Frontend Setup

1. **Run the setup script:**
   ```bash
   # On Linux/Mac:
   chmod +x setup_frontend.sh
   ./setup_frontend.sh
   
   # On Windows:
   setup_frontend.bat
   ```

2. **Create `.env` file in frontend directory (if not auto-created):**
   ```env
   VITE_API_URL=http://127.0.0.1:8000
   ```

3. **Start the frontend development server:**
   ```bash
   cd frontend
   npm run dev
   ```

The frontend will be available at `http://localhost:5173` (or the port shown in terminal)

## Manual Setup

### Backend

1. Create virtual environment:
   ```bash
   python -m venv backend/venv
   source backend/venv/bin/activate  # On Windows: backend\venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Download spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

4. Create `.env` file in project root with your Gemini API key

5. Start server:
   ```bash
   uvicorn main:app --reload
   ```

### Frontend

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Create `.env` file with `VITE_API_URL=http://127.0.0.1:8000`

3. Start development server:
   ```bash
   npm run dev
   ```

## API Endpoints

### Resume
- `POST /api/resume/upload` - Upload and parse a resume
- `POST /api/resume/score` - Get ATS score for a resume
- `POST /api/resume/feedback` - Get improvement feedback

### Interview
- `POST /api/interview/questions` - Generate interview questions
- `POST /api/interview/evaluate` - Evaluate an interview answer

### Voice
- `POST /api/voice/tts` - Text-to-speech
- `POST /api/voice/stt` - Speech-to-text
- `GET /api/voice/voices` - List available voices

### Health
- `GET /health` - Health check endpoint

## Project Structure

```
CAMPUSHIRE.AI2/
├── backend/
│   ├── api/           # API route handlers
│   ├── services/      # Business logic (parsing, scoring, etc.)
│   ├── models/        # Pydantic schemas
│   ├── data/          # Data files (skills.json, sample resumes)
│   └── main.py        # FastAPI application entry point
├── frontend/
│   ├── src/
│   │   ├── pages/     # React page components
│   │   ├── components/# Reusable components
│   │   └── lib/        # API client and utilities
│   └── package.json
└── .env               # Backend environment variables
```

## Troubleshooting

### Backend Issues

1. **"GEMINI_API_KEY is not set"**
   - Ensure `.env` file exists in project root
   - Check that `GEMINI_API_KEY` is set correctly

2. **"English language model not found"**
   - Run: `python -m spacy download en_core_web_sm`
   - Ensure you're in the virtual environment

3. **Import errors**
   - Ensure virtual environment is activated
   - Run: `pip install -r requirements.txt`

### Frontend Issues

1. **Cannot connect to backend**
   - Check `VITE_API_URL` in `frontend/.env`
   - Ensure backend is running on the specified port
   - Check CORS settings in backend

2. **API calls failing**
   - Check browser console for errors
   - Verify backend is running and accessible
   - Check network tab for request/response details

## Development

### Running Tests

```bash
cd backend
pytest
```

### Code Formatting

```bash
cd backend
black .
isort .
```

## License

This project is for educational purposes.

## Support

For issues and questions, please check the troubleshooting section or review the API documentation at `http://127.0.0.1:8000/docs` when the backend is running.
