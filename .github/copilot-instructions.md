<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Personal AI Assistant - Copilot Instructions

This is a comprehensive personal AI assistant project designed for document analysis, business intelligence, and personal organization.

## Project Structure

- **Backend**: FastAPI with Python
- **Frontend**: Streamlit web interface
- **AI**: OpenAI GPT models
- **Vector Database**: ChromaDB for document storage
- **Document Processing**: Support for XLS, Word, PDF, CSV files
- **Business Analytics**: Financial data analysis and forecasting

## Key Components

1. **Document Processing** (`core/document_processor.py`):
   - Handles XLS, Word, PDF, CSV, and text files
   - Extracts content and creates searchable chunks
   - Preserves document metadata

2. **Vector Store** (`core/vector_store.py`):
   - Uses ChromaDB for vector storage
   - Generates embeddings with OpenAI
   - Enables semantic search across documents

3. **Chat Engine** (`core/chat_engine.py`):
   - Main AI interaction logic
   - Context-aware responses
   - Business query detection

4. **Business Tools** (`utils/business_tools.py`):
   - Financial data analysis
   - Expense categorization
   - Simple forecasting
   - Business insights generation

5. **API Layer** (`api/routes.py`):
   - RESTful endpoints
   - File upload handling
   - Error management

## Development Guidelines

### Code Style
- Use type hints for all functions
- Include comprehensive docstrings
- Handle exceptions gracefully
- Log important operations

### AI Integration
- Always validate OpenAI API key
- Handle rate limits and errors
- Use appropriate temperature settings
- Implement context window management

### Document Processing
- Support multiple file formats
- Validate file sizes and types
- Create meaningful text chunks
- Preserve document structure

### Business Features
- Auto-categorize expenses
- Detect financial columns
- Generate actionable insights
- Support time series analysis

### Error Handling
- Provide user-friendly error messages
- Log detailed error information
- Implement graceful degradation
- Validate all inputs

## Configuration

- Environment variables in `.env` file
- Settings centralized in `config/settings.py`
- Configurable chunk sizes and models
- Flexible file upload limits

## Security Considerations

- Secure file uploads with validation
- Sanitize user inputs
- Protect API endpoints
- Handle sensitive financial data appropriately

## Testing

- Test all file format processing
- Verify AI response quality
- Check business analysis accuracy
- Validate API endpoints

When working on this project, prioritize:
1. User experience and ease of use
2. Accurate document processing
3. Relevant AI responses
4. Business insight quality
5. System reliability
