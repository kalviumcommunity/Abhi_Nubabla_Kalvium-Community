# RAG Streaming & Citations Implementation Guide

## Overview

This implementation adds **progressive answer streaming** and **clear citation display** to the RAG Chat UI, allowing users to:

1. ✅ **See answers appear progressively** instead of waiting for complete responses
2. ✅ **View citations with source markers** (`[1]`, `[2]`, etc.)
3. ✅ **Click citations to view full source content**
4. ✅ **Handle streaming errors gracefully** without UI breakage

## Architecture

### Backend (FastAPI)

#### New Endpoint: `/query/stream`
- **Method**: `POST`
- **Protocol**: Server-Sent Events (SSE)
- **Response Format**: Newline-delimited JSON events

#### Event Types

The streaming endpoint yields several event types:

```json
// 1. Initial metadata
{
  "type": "metadata",
  "request_id": "uuid",
  "timestamp": "ISO-8601",
  "query": "user question"
}

// 2. Status updates
{
  "type": "status",
  "message": "Retrieved 3 relevant sources",
  "status": "processing|generating|complete"
}

// 3. Answer chunks (streamed word-by-word)
{
  "type": "answer_chunk",
  "chunk": "word "
}

// 4. Citation metadata (after answer)
{
  "type": "citation",
  "tag": "[1]",
  "metadata": {
    "index": 1,
    "source_document": "employee_benefits.md",
    "section": "PTO Policy",
    "page": 5,
    "similarity_score": 0.9234,
    "chunk_id": "chunk_001",
    "token_count": 150,
    "full_source_text": "..."
  }
}

// 5. Completion
{
  "type": "complete",
  "status": "success",
  "request_id": "uuid"
}

// 6. Error (if stream fails)
{
  "type": "error",
  "message": "Error description",
  "error_code": "ERROR_TYPE",
  "status": "failed"
}
```

### Frontend (HTML/CSS/JS)

#### Key Components

1. **Chat Interface** (`chat_ui.html`)
   - Displays user messages and streaming assistant responses
   - Shows progressive answer text as chunks arrive
   - Renders citation metadata below answers
   - Manages modal for viewing full source content

2. **Features**
   - Progressive answer display (word-by-word streaming)
   - Citation markers with metadata
   - Clickable citations to view full source
   - Real-time status updates
   - Error handling and display
   - Responsive design (mobile-friendly)

## Files Modified/Created

### Backend Changes

#### `src/api.py`
- **Added**: `StreamingResponse` import
- **Added**: `generate_streaming_response()` async generator
- **Added**: `/query/stream` endpoint (POST)
- **Modified**: Added streaming helper functions

### New Files

#### `chat_ui.html`
- Complete standalone HTML interface with embedded CSS and JavaScript
- Single-file deployment (no build step needed)
- Features:
  - Beautiful gradient UI with modern design
  - Progressive answer streaming display
  - Citation panel with source metadata
  - Modal popup for viewing full source text
  - Error messages and status updates
  - Responsive layout

#### `streaming_demo.py`
- Demo script to test streaming functionality
- Showcases multiple queries
- Rich formatted output with tables and colors
- Error handling for common issues

## Usage

### Starting the API

```bash
# Make sure .env is configured with OPENAI_API_KEY
python -m src.api
```

The API will start on `http://localhost:8000`

Endpoints:
- Health check: `GET http://localhost:8000/health`
- Config: `GET http://localhost:8000/config`
- Streaming query: `POST http://localhost:8000/query/stream`

### Using the Web UI

1. **Open in Browser**
   ```bash
   # Simply open the HTML file in your browser
   chat_ui.html
   # Or serve it via HTTP
   python -m http.server 8080
   # Then visit http://localhost:8080/chat_ui.html
   ```

2. **Interact with Chat**
   - Type a question in the input field
   - Click "Send" or press Enter
   - Watch the answer stream in progressively
   - Click any `[1]`, `[2]`, etc. citation to view full source
   - Citations appear below the answer with relevance scores

3. **Citations Panel**
   - Shows ranked source documents
   - Displays section name, page number (if available)
   - Shows relevance confidence as percentage
   - Clickable to expand and view full content

### Running the Demo Script

```bash
# Install dependencies if needed
pip install httpx rich

# Run the demo
python streaming_demo.py
```

The demo will:
- Send 3 sample queries to the API
- Display progressive streaming responses
- Show citation metadata as it arrives
- Format results with tables and colors

## API Usage Example (Python)

```python
import httpx
import json

async def stream_query():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/query/stream",
            json={"question": "What is the password policy?", "k": 3}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    event = json.loads(line[6:])
                    
                    if event["type"] == "answer_chunk":
                        print(event["chunk"], end="")
                    elif event["type"] == "citation":
                        print(f"\nSource: {event['metadata']['source_document']}")

# Run it
asyncio.run(stream_query())
```

## Error Handling

### Backend Errors
The streaming endpoint handles:
- ❌ **Vector store not found** → Error event with VECTOR_STORE_NOT_FOUND
- ❌ **Invalid request** → HTTP 400 before stream starts
- ❌ **Pipeline failures** → Error event in stream
- ❌ **Network timeouts** → Stream closes gracefully

### Frontend Error Display
- Red error messages in chat area
- Connection retry-friendly UI (users can try again)
- User-friendly error descriptions
- Clear guidance on what went wrong

## Performance Considerations

### Streaming Benefits
- ✅ **Perceived Performance**: Users see content immediately
- ✅ **Better UX**: Progressive content feels faster
- ✅ **Mobile Friendly**: Can stop/resume connection
- ✅ **Bandwidth Efficient**: No buffering large responses

### Current Implementation
- Word-by-word streaming with 10ms delays (configurable)
- Citations sent after answer completion
- Full source text included with citations

### Future Optimizations
- Token-level streaming instead of word-level
- Streaming citations alongside answer
- Compression for large source texts
- Connection pooling for multiple queries

## Configuration

### Environment Variables

```bash
# .env file
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4-turbo
VECTOR_STORE_PATH=data/embedded_chunks.json
RETRIEVAL_K=3
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

### Streaming Delays

In `src/api.py`, adjust the streaming delay:
```python
await asyncio.sleep(0.01)  # 10ms between chunks - adjust to taste
```

## Browser Compatibility

✅ Works on:
- Chrome/Chromium (v60+)
- Firefox (v55+)
- Safari (v12+)
- Edge (v79+)
- Mobile browsers

Requires:
- Modern JavaScript (ES6+)
- Fetch API with streaming support
- EventSource or manual SSE parsing

## Testing

### Health Check
```bash
curl http://localhost:8000/health
```

### Config Check
```bash
curl http://localhost:8000/config
```

### Test Streaming (cURL)
```bash
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "What is PTO policy?", "k": 3}'
```

Should see streaming JSON events.

## Debugging

### Enable API Logging
```bash
LOG_LEVEL=DEBUG python -m src.api
```

### Browser Console
Open DevTools (F12) and check Console tab for:
- Network requests
- Event parsing errors
- Citation data logging

### Demo Script Verbose Output
```bash
python streaming_demo.py 2>&1 | head -100
```

## Known Limitations

1. **Source Text Truncation**: Very large source texts may take longer to stream
2. **Citation Timing**: Citations appear after answer (design choice for UX)
3. **Concurrency**: Single query at a time per session (by design)
4. **Browser Support**: Requires modern browser with Fetch API

## Future Enhancements

- [ ] Streaming citations alongside answer text
- [ ] Voice input for questions
- [ ] Save conversation history
- [ ] Export answers with citations
- [ ] Source highlighting in answer text
- [ ] Citation count and ranking metrics
- [ ] Dark mode UI
- [ ] Multi-language support

## Troubleshooting

### "Connection refused" error
- **Check**: Is the API running? `python -m src.api`
- **Check**: Is it on the right port? Default: 8000

### No streaming chunks appear
- **Check**: Is OPENAI_API_KEY set? See `/config` endpoint
- **Check**: Does vector store exist? `data/embedded_chunks.json`
- **Check**: Browser console for errors (F12)

### Citations not showing
- **Check**: Did the query retrieve sources? Check backend logs
- **Check**: Are citations in the answer text? Some answers may not have citations

### Slow streaming
- **Adjust**: Streaming delay in `src/api.py` (line ~475)
- **Note**: 10ms delays are just for demo; production can be faster

## License & Attribution

This implementation extends the RAG Pipeline API with:
- FastAPI streaming responses via SSE
- Modern web UI with real-time updates
- Citation tracking and source viewing

Built on top of:
- OpenAI GPT models
- Chroma/similarity search
- FastAPI framework
- Rich library for CLI output
