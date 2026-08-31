import os
import sys
import json
import pypdf

# Configure stdout/stderr to use UTF-8 to prevent encoding issues on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

def main():
    print("==================================================")
    print("      RAG Chunk Traceability Demonstration      ")
    print("==================================================\n")

    chunks_json_path = "data/sample_chunks.json"
    if not os.path.exists(chunks_json_path):
        print(f"Error: {chunks_json_path} does not exist. Run document_loader.py first.")
        return

    with open(chunks_json_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks from {chunks_json_path}.\n")

    # We will pick representative chunks (one of each file type) to demonstrate tracing
    demo_indices = []
    seen_types = set()
    for idx, chunk in enumerate(chunks):
        source = chunk["metadata"]["source"]
        _, ext = os.path.splitext(source)
        if ext not in seen_types:
            seen_types.add(ext)
            demo_indices.append(idx)

    # Let's make sure we show at least one of each: .txt, .md, .html, .pdf
    for i, idx in enumerate(demo_indices, 1):
        chunk = chunks[idx]
        text = chunk["text"]
        meta = chunk["metadata"]
        source = meta["source"]
        section = meta["section"]
        page = meta["page"]
        pos = meta["position"]

        print(f"--- Demonstration {i}: Tracing Chunk from {source} ---")
        print(f"Chunk Text Preview: \"{text[:60].replace(chr(10), ' ')}...\"")
        print(f"Metadata: Section='{section}', Page={page}, Position={pos}\n")

        # Let's trace it!
        if not os.path.exists(source):
            print(f"Warning: Source file {source} not found locally.\n")
            continue

        _, ext = os.path.splitext(source)
        ext = ext.lower()

        if ext in [".txt", ".md"]:
            # For plain text and markdown, we seek to pos in raw content
            with open(source, "r", encoding="utf-8", errors="replace") as sf:
                raw_content = sf.read()
            
            # Extract text from raw content at pos
            extracted = raw_content[pos:pos+len(text)]
            # Also get a surrounding snippet
            start_context = max(0, pos - 30)
            end_context = min(len(raw_content), pos + len(text) + 30)
            context = raw_content[start_context:end_context]
            
            print(f"Original Raw Content at Position {pos} (with surrounding context):")
            print("----------------------------------------")
            print(context)
            print("----------------------------------------")
            
            # Verify match
            if text.strip().replace("\r\n", "\n") in raw_content.replace("\r\n", "\n"):
                print("✅ TRACE SUCCESS: Chunk text exists in source file.")
                if text.strip()[:10] in extracted.strip()[:10]:
                    print("✅ POSITION ALIGNED: Offset matches start of chunk text perfectly!\n")
                else:
                    print("⚠️ POSITION DRIFT: Text exists in file but offset is slightly shifted.\n")
            else:
                print("❌ TRACE FAILURE: Chunk text not found in source file.\n")

        elif ext in [".html", ".htm"]:
            # For HTML, we seek to pos in raw HTML content
            with open(source, "r", encoding="utf-8", errors="replace") as sf:
                raw_html = sf.read()
            
            extracted = raw_html[pos:pos+len(text)]
            start_context = max(0, pos - 30)
            end_context = min(len(raw_html), pos + len(text) + 30)
            context = raw_html[start_context:end_context]
            
            print(f"Original Raw HTML Snippet at Position {pos} (with surrounding tags):")
            print("----------------------------------------")
            print(context)
            print("----------------------------------------")
            
            if text[:20] in raw_html:
                print("✅ TRACE SUCCESS: Chunk text found within raw HTML content.")
                if text[:10] in extracted:
                    print("✅ POSITION ALIGNED: Offset matches start of text inside tags perfectly!\n")
                else:
                    print("⚠️ POSITION DRIFT: Text exists inside HTML but offset tag boundary varies.\n")
            else:
                print("❌ TRACE FAILURE: Text not found in raw HTML.\n")

        elif ext == ".pdf":
            # For PDF, we trace back to specific page and offset in page's text
            reader = pypdf.PdfReader(source)
            page_text = reader.pages[page - 1].extract_text()
            
            extracted = page_text[pos:pos+len(text)]
            start_context = max(0, pos - 30)
            end_context = min(len(page_text), pos + len(text) + 30)
            context = page_text[start_context:end_context]
            
            print(f"Extracted PDF Page {page} Text at Offset {pos}:")
            print("----------------------------------------")
            print(context)
            print("----------------------------------------")
            
            if text.strip() in page_text:
                print("✅ TRACE SUCCESS: Chunk text found in PDF Page text.")
                if text.strip()[:10] in extracted.strip()[:10]:
                    print("✅ POSITION ALIGNED: Offset matches start of text on page perfectly!\n")
                else:
                    print("⚠️ POSITION DRIFT: Text exists on page but offset layout differs slightly.\n")
            else:
                print("❌ TRACE FAILURE: Text not found in PDF page text.\n")
        
        print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
