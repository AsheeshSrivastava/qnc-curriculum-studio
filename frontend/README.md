# Python Research Portal - Frontend

Beautiful Streamlit UI for the Python Research Portal backend.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Backend API running on `http://127.0.0.1:8000`

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure backend URL (optional):**
   ```bash
   cp config.env.example config.env
   # Edit config.env to set BACKEND_URL if different from default
   ```

3. **Run the app:**
   ```bash
   streamlit run app.py
   ```

4. **Open your browser:**
   Navigate to `http://localhost:8501`

## 📁 Project Structure

```
frontend/
├── app.py                      # Main entry point (Home page)
├── pages/                      # Multi-page app
│   ├── 1_📄_Upload.py         # Document upload interface
│   ├── 2_💬_Chat.py           # Chat interface with AI
│   ├── 3_📚_Library.py        # Document library browser
│   └── 4_⚙️_Settings.py       # API key & provider settings
├── components/                 # Reusable UI components
│   └── sidebar.py             # Sidebar with navigation
├── utils/                      # Utility modules
│   ├── api_client.py          # Backend API client
│   └── session.py             # Session state management
├── .streamlit/                 # Streamlit configuration
│   └── config.toml            # Theme & server settings
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🎨 Features

### 📄 Document Upload
- Drag-and-drop file upload
- Support for PDF, Markdown, and JSON
- Custom titles and descriptions
- Real-time processing feedback
- Recent uploads view

### 💬 Chat Interface
- Clean chat UI with message history
- Streaming response support
- Citation display
- Quality evaluation metrics
- Export to Markdown/JSON/PDF

### 📚 Document Library
- Browse all uploaded documents
- Search and filter
- Sort by date or title
- Document details view
- Quick actions

### ⚙️ Settings
- Secure API key management
- Multi-provider support (OpenAI, Gemini, OpenRouter)
- Provider selection
- System information

## 🔑 API Key Configuration

### Option 1: Via UI (Recommended)
1. Go to **Settings** page
2. Enter your API key for your preferred provider
3. Click **Save**

### Option 2: Environment Variables
```bash
# In config.env
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
```

## 🎨 Customization

### Theme
Edit `.streamlit/config.toml` to customize colors and fonts:

```toml
[theme]
primaryColor = "#4F46E5"        # Indigo
backgroundColor = "#FFFFFF"      # White
secondaryBackgroundColor = "#F3F4F6"  # Gray
textColor = "#1F2937"           # Dark Gray
font = "sans serif"
```

### Branding
- Add your logo to `assets/logo.png`
- Update the title in `app.py`
- Customize the sidebar in `components/sidebar.py`

## 🚀 Deployment

### Streamlit Community Cloud (Recommended)

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add Streamlit frontend"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub repository
   - Select `frontend/app.py` as the main file
   - Deploy!

3. **Configure secrets:**
   - In Streamlit Cloud dashboard, go to Settings > Secrets
   - Add your backend URL:
     ```toml
     BACKEND_URL = "https://your-backend-url.com"
     ```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t research-portal-frontend .
docker run -p 8501:8501 -e BACKEND_URL=http://backend:8000 research-portal-frontend
```

## 🔧 Development

### Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run with auto-reload
streamlit run app.py

# Run on custom port
streamlit run app.py --server.port 8502
```

### Adding New Pages
1. Create a new file in `pages/` with format: `N_emoji_Name.py`
2. Import required utilities:
   ```python
   from components.sidebar import render_sidebar
   from utils.session import init_session_state
   ```
3. Initialize and render:
   ```python
   init_session_state()
   render_sidebar()
   ```

## 📊 Performance Tips

1. **Use caching:**
   ```python
   @st.cache_data
   def expensive_function():
       # ...
   ```

2. **Optimize API calls:**
   - Cache API client with `@st.cache_resource`
   - Batch requests when possible
   - Use session state for temporary data

3. **Lazy loading:**
   - Load documents on demand
   - Paginate large lists
   - Use expanders for heavy content

## 🐛 Troubleshooting

### Backend Connection Failed
- Check if backend is running: `curl http://127.0.0.1:8000/api/health`
- Verify `BACKEND_URL` in config
- Check firewall/network settings

### API Key Not Working
- Ensure key is correctly entered (no extra spaces)
- Verify key is valid on provider's website
- Check provider is selected in Settings

### Slow Performance
- Enable caching for API calls
- Reduce document list limit
- Use streaming mode for chat

## 📝 License

© 2025 Python Research Portal. All rights reserved.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📞 Support

- [Documentation](#)
- [GitHub Issues](#)
- [Discord Community](#)




