# RAG Streaming Quick Start Guide

Get streaming responses with citations working in 5 minutes!

## Quick Start (Windows/Mac/Linux)

### 1️⃣ Start the API Server

```bash
cd /path/to/project
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

**Expected output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 2️⃣ Open the Chat Interface

Open `ui.html` in your browser:
- **Method 1**: Right-click on `ui.html` → "Open with" → Your browser
- **Method 2**: 
  - Windows: `start ui.html`
  - Mac: `open ui.html`
  - Linux: `xdg-open ui.html`

### 3️⃣ Ask a Question

1. Click in the text box at the bottom
2. Type: "What is the company PTO policy?"
3. Press **Enter** or click **Send**
4. Watch the answer stream in progressively! 🎯

## What You'll See

### Progressive Streaming
```
According to company policy... [appears letter by letter]
```

### Citation Markers
```
...18 days of PTO annually [1]. PTO accrues monthly [2]...
```

Click [1], [2], etc. to see source details!

### Source Sidebar
Right panel shows:
- Document name and section
- Relevance score
- Chunk ID
- Click to expand for more info

## Test Queries

Try these questions to see streaming in action:

1. "What is the company PTO policy?"
2. "How should I report a security incident?"
3. "What VPN requirements do we have?"
4. "What's the remote work policy?"

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "Cannot connect to API" | Make sure API server is running on port 8000 |
| "No sources appear" | Check that vector store exists at `data/embedded_chunks.json` |
| "Answer is blank" | Check API key is set in `.env` file |
| "Citations not showing" | Reload the page and try again |

## Feature Checklist

✅ Answers stream token-by-token (not waiting for full completion)
✅ Citation markers [1], [2] appear inline in answer  
✅ Click citations to see source document details
✅ Sources display in right sidebar with metadata
✅ Click sources to expand and see full information
✅ Error messages show clearly if something fails
✅ UI stays responsive during streaming

## Network Requirements

- Local API: No internet required
- Remote API: Ensure firewall allows port 8000
- Browser: Modern browser with SSE support (Chrome, Firefox, Safari, Edge)

## Customization

### Change Port
```bash
python -m uvicorn src.api:app --host 127.0.0.1 --port 9000
```
Then update `ui.html` line 215: `const API_BASE_URL = 'http://localhost:9000';`

### Change Number of Sources
In `ui.html` line 424:
```javascript
// Change k parameter (default is 3)
body: JSON.stringify({
    question: question,
    k: 5,  // Retrieve 5 sources instead of 3
    score_threshold: 0.0
})
```

### Change Citation Frequency
In `src/streaming_generator.py` around line 204:
```python
# Inject citations every N tokens (default is ~30)
if token_count % 20 == 0:  # More frequent citations
    should_cite = True
```

## API Health Check

Verify API is working:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "RAG Pipeline API",
  "version": "1.0.0"
}
```

## Next Steps

1. ✅ Try streaming with different questions
2. 📚 Review [STREAMING_IMPLEMENTATION_GUIDE.md](STREAMING_IMPLEMENTATION_GUIDE.md) for detailed docs
3. 📊 Check [STREAMING_DEMO_OUTPUT.md](STREAMING_DEMO_OUTPUT.md) for example outputs
4. 🔧 Customize UI colors, fonts, or layout in `ui.html`
5. 📦 Deploy to production with Docker (if needed)

## File Reference

```
ui.html                    ← Open this in browser
src/api.py                 ← API server (running on port 8000)
src/streaming_generator.py ← Streaming logic
streaming_demo.py          ← Python test script
```

## Performance Tips

- **Faster responses**: Reduce `k` parameter (fewer sources to retrieve)
- **Better accuracy**: Increase `k` (more sources but slower)
- **Smoother UI**: Use a modern browser (Chrome/Firefox faster than Safari)
- **Lower latency**: Run API on same machine as browser

## Keyboard Shortcuts (UI)

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Shift+Enter` | New line in input |
| Click [1], [2], etc. | View source details |
| Click source item | Expand/collapse source |

---

**You're all set!** 🚀

The streaming RAG is now running with citations. Enjoy progressive answer streaming with source verification!

For more details, see:
- 📖 [STREAMING_IMPLEMENTATION_GUIDE.md](STREAMING_IMPLEMENTATION_GUIDE.md)
- 📊 [STREAMING_DEMO_OUTPUT.md](STREAMING_DEMO_OUTPUT.md)
