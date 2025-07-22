# Personal AI Assistant

A comprehensive AI-powered assistant for document analysis, business planning, research, and personal organization.

## Features

- 📄 **Document Analysis**: Process XLS, Word, PDF files
- 🤖 **AI Chat Interface**: Intelligent conversations with context
- 📊 **Business Tools**: Expense tracking, forecasting, planning
- 🔍 **Research Assistant**: Academic and business research support
- 📝 **Writing Helper**: Diary organization, homework assistance
- 🗂️ **File Management**: Upload and organize documents
- 💾 **Vector Database**: Persistent memory and document storage

## Technologies Used

- **Backend**: FastAPI (Python)
- **AI**: OpenAI GPT models
- **Vector DB**: ChromaDB
- **Document Processing**: python-docx, openpyxl, PyPDF2
- **Frontend**: Streamlit web interface
- **Data Analysis**: pandas, matplotlib, plotly

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment**:
   ```bash
   cp .env.example .env
   # Add your OpenAI API key to .env
   ```

3. **Run the Application**:
   
   **Option A: Standalone App (Recommended for Deployment)**:
   ```bash
   streamlit run app.py
   ```
   
   **Option B: Full Stack (API + Frontend)**:
   ```bash
   # Start the API server
   python main.py
   
   # In another terminal, start the web interface
   streamlit run streamlit_app.py
   ```

4. **Access the Application**:
   - API Documentation: <http://localhost:8000/docs>
   - Web Interface: <http://localhost:8501>

## 🚀 Deploy Live (Cloud Hosting)

### Quick Deploy to Streamlit Cloud (FREE)

1. **Get OpenAI API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create new API key

2. **Deploy to Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file: `app.py`
   - Add secret: `OPENAI_API_KEY = "your_key_here"`
   - Click Deploy!

3. **Your app will be live** at: `https://your-app-name.streamlit.app`

### Other Deployment Options

- **Heroku**: See `DEPLOYMENT.md` for detailed instructions
- **Railway**: Simple deployment with GitHub integration
- **Google Cloud Run**: Enterprise-grade hosting
- **Local Network**: Access from other devices on your network

**📚 Full deployment guide**: See `DEPLOYMENT.md` and `QUICK_DEPLOY.md`

## Usage

### Document Upload
1. Use the web interface to upload XLS, DOCX, or PDF files
2. The system automatically processes and indexes the content
3. Ask questions about your documents through the chat interface

### Business Features
- **Expense Tracking**: Upload receipts and bills for automatic categorization
- **Forecasting**: Analyze trends in your business data
- **Planning**: Organize ideas and create structured plans

### Research & Writing
- **Academic Research**: Analyze papers and documents for grad school prep
- **Writing Assistant**: Get help with essays, reports, and creative writing
- **Diary Organization**: Structure and analyze personal notes

## File Structure

```
ChatBotFinal/
├── main.py                 # FastAPI server
├── streamlit_app.py        # Web interface
├── config/
│   └── settings.py         # Configuration
├── core/
│   ├── chat_engine.py      # Main chat logic
│   ├── document_processor.py # File processing
│   └── vector_store.py     # Vector database
├── models/
│   └── schemas.py          # Data models
├── api/
│   └── routes.py           # API endpoints
├── utils/
│   ├── file_handlers.py    # File processing utilities
│   └── business_tools.py   # Business analysis tools
├── templates/              # HTML templates
├── static/                 # CSS/JS files
├── uploads/                # Uploaded files
└── data/                   # Database and storage
```

## Environment Variables

Create a `.env` file with the following:

```
OPENAI_API_KEY=your_openai_api_key_here
CHROMA_DB_PATH=./data/chroma_db
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=50MB
DEBUG=True
```

## API Endpoints

- `POST /chat` - Send messages to the AI
- `POST /upload` - Upload documents
- `GET /documents` - List uploaded documents
- `POST /analyze/business` - Business data analysis
- `POST /analyze/research` - Research document analysis

## Contributing

This is a personal project, but feel free to fork and customize for your needs.

## License

MIT License - See LICENSE file for details.
