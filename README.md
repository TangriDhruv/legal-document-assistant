# 📋 Legal Document Assistant

An AI-powered document completion tool that intelligently fills in document placeholders through natural conversation. Upload a `.docx` file, chat with an AI assistant to provide information, and download your completed document.

**🌐 Live Demo**: [https://legal-document-assistant-chi.vercel.app/](https://legal-document-assistant-chi.vercel.app/)

---

## ✨ Features

- **📄 Document Upload**: Upload `.docx` files with document placeholders (e.g., `[Company Name]`, `[Date]`)
- **🤖 AI-Powered Detection**: Automatically detects and extracts all placeholders from your document
- **💬 Conversational Interface**: Chat naturally with an AI assistant to fill document fields
- **🎯 Smart Field Matching**: LLM uses context to understand which field you're describing
- **📊 Progress Tracking**: Visual progress bar and field list to track completion status
- **⬇️ Download**: Generate and download your completed document with all fields filled
- **🎨 Modern Dark UI**: ChatGPT-style interface with responsive design
- **📱 Mobile Friendly**: Works seamlessly on desktop, tablet, and mobile devices

---

## 🏗️ Tech Stack

### Frontend
- **React 19** with TypeScript
- **Vite** - Lightning-fast build tool
- **CSS3** - Custom dark theme styling
- **Axios** - HTTP client for API calls

### Backend
- **FastAPI** - Modern async Python web framework
- **OpenAI API** - GPT-4 Mini for intelligent field extraction
- **LangChain** - LLM orchestration and prompting
- **python-docx** - DOCX file manipulation
- **Pydantic** - Data validation

### Deployment
- **Frontend**: Vercel
- **Backend**: Render/Railway/Docker-ready

---

## 📁 Project Structure

```
legal-document-assistant/
├── frontend/                    # React application
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── FileUpload.tsx
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── PlaceholderList.tsx
│   │   │   └── ProgressBar.tsx
│   │   ├── hooks/
│   │   │   └── useDocumentSession.ts  # Main session logic
│   │   ├── types/
│   │   │   └── index.ts        # TypeScript interfaces
│   │   ├── App.tsx             # Main app component
│   │   ├── App.css             # Dark theme styling
│   │   └── main.tsx
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── package.json
│   └── index.html
│
├── backend/                     # FastAPI application
│   ├── main.py                 # FastAPI app & endpoints
│   ├── config.py               # Configuration & settings
│   ├── models.py               # Pydantic data models
│   ├── document_handler.py     # DOCX processing logic
│   ├── llm_handler.py          # OpenAI/LangChain integration
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Docker configuration
│   ├── Procfile                # Render deployment config
│   └── .env.example
│
├── LICENSE
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **OpenAI API Key** ([Get one here](https://platform.openai.com/account/api-keys))

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Create environment file**
   ```bash
   cat > .env.local << EOF
   VITE_API_URL=http://localhost:8000
   EOF
   ```

4. **Start development server**
   ```bash
   npm run dev
   ```
   Opens at `http://localhost:5173`

5. **Build for production**
   ```bash
   npm run build
   ```

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file**
   ```bash
   cat > .env << EOF
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-4-mini
   PORT=8000
   DEBUG=false
   EOF
   ```
   > ⚠️ Replace `sk-your-key-here` with your actual OpenAI API key

5. **Run development server**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   API available at `http://localhost:8000`

6. **Check health endpoint**
   ```bash
   curl http://localhost:8000/health
   ```

---

## 🔑 Environment Variables

### Backend (.env)

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-mini                    # Model to use
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2048

# Optional: LangChain Monitoring
LANGCHAIN_TRACING_V2=false
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-key-here
LANGCHAIN_PROJECT=legal-doc-assistant

# Server Configuration
PORT=8000
DEBUG=false

# Document Configuration
MAX_FILE_SIZE_MB=50
SESSION_TIMEOUT_MINUTES=60
```

### Frontend (.env.local)

```env
VITE_API_URL=http://localhost:8000         # Backend API URL
```

---

## 📡 API Endpoints

### POST `/upload`
Upload and parse a `.docx` file

**Request:**
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@document.docx"
```

**Response:**
```json
{
  "session_id": "uuid-string",
  "filename": "document.docx",
  "placeholders": [
    {
      "name": "Company Name",
      "context": "...surrounding text...",
      "filled": false,
      "description": "Please provide: company name"
    }
  ]
}
```

### POST `/chat`
Chat to fill document fields

**Request:**
```json
{
  "session_id": "uuid-string",
  "message": "The company is Acme Corp",
  "placeholders": [...]
}
```

**Response:**
```json
{
  "assistant_message": "Got it, company is Acme Corp.",
  "filled_values": {"Company Name": "Acme Corp"},
  "placeholders": [...],
  "next_question": null
}
```

### POST `/download`
Download completed document

**Request:**
```json
{
  "session_id": "uuid-string"
}
```

**Response:** Binary `.docx` file

### GET `/status/{session_id}`
Get session progress

**Response:**
```json
{
  "session_id": "uuid-string",
  "progress": "5/10",
  "completed": false,
  "placeholders": [...]
}
```

### GET `/health`
Health check

---

## 💡 How It Works

1. **Upload**: User uploads a `.docx` file containing placeholders like `[Company Name]`
2. **Detection**: System extracts all placeholders and analyzes their context
3. **Conversation**: User provides information through natural language chat
4. **Matching**: AI matches user input to specific document fields
5. **Extraction**: Values are extracted and associated with exact placeholder names
6. **Completion**: User downloads document with all placeholders replaced
7. **Download**: Completed document preserves original formatting

### Example Workflow

```
User uploads: contract.docx with [Company Name], [Date], [Signatory Name]
                          ↓
System detects 3 placeholders
                          ↓
User: "The company is Acme Corp"
AI: "Got it, company is Acme Corp"
                          ↓
User: "Date is January 15, 2025"
AI: "Noted, date is January 15, 2025"
                          ↓
User: "Signatory is John Smith"
AI: "Confirmed, signatory is John Smith"
                          ↓
User clicks "Download"
                          ↓
System replaces placeholders and returns completed PDF
```

---

## 🚀 Deployment

### Deploy Frontend (Vercel)

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Set root directory: `./frontend`

3. **Configure environment**
   - Add `VITE_API_URL` pointing to your backend URL

4. **Deploy**
   ```bash
   vercel deploy --prod
   ```

### Deploy Backend (Render)

1. **Create Render account** at [render.com](https://render.com)

2. **Create new Web Service**
   - Connect GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add environment variables**
   - `OPENAI_API_KEY`
   - `OPENAI_MODEL`
   - `PORT=8000`

4. **Deploy**
   - Render auto-deploys on GitHub push

### Docker Deployment

**Build image:**
```bash
cd backend
docker build -t legal-doc-assistant .
```

**Run container:**
```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e OPENAI_MODEL=gpt-4-mini \
  legal-doc-assistant
```

---

## 🛠️ Development

### Run both frontend and backend concurrently

```bash
# Terminal 1: Frontend
cd frontend && npm run dev

# Terminal 2: Backend
cd backend && source venv/bin/activate && uvicorn main:app --reload
```

### Debugging

**Backend debug logging:**
```python
# In llm_handler.py
DEBUG = True  # Enables detailed logs
```

**Check session state:**
```bash
curl http://localhost:8000/debug/{session_id}
```

### Testing

```bash
# Frontend tests
cd frontend && npm run lint

# Backend - add pytest and run
pip install pytest
pytest
```

---

## 📝 Supported Document Format

- **File type**: `.docx` (Microsoft Word format only)
- **Max file size**: 50 MB
- **Placeholder format**: `[Placeholder Name]`
- **Placeholder examples**:
  - `[Company Name]`
  - `[Date of Execution]`
  - `[Investor Name]`
  - `[Amount]`
  - `[Address]`

---

## 🔒 Security & Limitations

- ✅ Session data stored in-memory (clears on server restart)
- ✅ CORS enabled for cross-origin requests
- ⚠️ No user authentication (for demo purposes)
- ⚠️ Files automatically cleaned up after session timeout (60 min default)
- ⚠️ API rate limits depend on OpenAI tier

---

## 🤝 Contributing

Contributions welcome! Please follow these steps:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

### Development Guidelines
- Follow existing code style
- Add TypeScript types for all functions
- Test changes locally before submitting PR
- Update README if adding new features

---

## 🐛 Troubleshooting

### "OpenAI API Key not found"
- Check `.env` file exists in backend directory
- Verify `OPENAI_API_KEY` is set correctly
- Don't include quotes around the key

### "CORS error when uploading"
- Make sure `VITE_API_URL` in frontend `.env.local` matches your backend URL
- Backend should have CORS middleware enabled (it does by default)

### "Placeholder not filling"
- Verify placeholder format: `[Exact Name]` (case-sensitive)
- Check document is valid `.docx` format
- Use `/debug/{session_id}` endpoint to see current state

### "Download button disabled"
- All placeholders must be filled (marked with ✅)
- Check sidebar for remaining unfilled fields
- If stuck, use "New Document" button to reset

---

## 📊 Performance Tips

- Keep document file size under 10 MB for faster processing
- Minimize number of placeholders (works best with 5-50 fields)
- Use clear placeholder names that describe the content
- OpenAI API calls are the main latency factor

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## 👤 Author

Created by Dhruv Tangri

---

**Made with ❤️ for legal professionals and document automation**
