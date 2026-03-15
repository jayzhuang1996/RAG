# Podcast RAG — Source Code Explanation Guide

This document walks through every Python file in `src/` line-by-line, with real examples to explain what each line does, which things come from libraries, which come from Python itself, and which are our own code.

---

## How to Read This Document

| Tag | Meaning |
|---|---|
| 🔵 **Library** | Third-party package from `requirements.txt` |
| 🟢 **Built-in** | Comes with Python — no install needed |
| 🟠 **Our Code** | We wrote this ourselves |
| ⚙️ **Concept** | Explains a deeper pattern or idea |

---

## File 1: `src/db.py` — The Database Foundation

**Role:** Every other file uses this. It defines the database location, how to connect to it, and what tables exist.

### Lines 1–3: Imports

```python
import sqlite3   # 🔵 Library (built-in to Python, no pip needed)
import json      # 🟢 Built-in
import os        # 🟢 Built-in
```

- **`sqlite3`** — Python ships with a full SQL database engine. No server needed. The whole database is one file: `data/podcasts.db`.
- **`json`** — Converts Python dicts to strings and back. We use it to store raw transcript data as text in the DB.
- **`os`** — Lets us build file paths, check if directories exist, etc.

### Lines 7–8: Finding the Project Root

```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, 'data', 'podcasts.db')
```

⚙️ **Concept — Why this pattern?**  
Imagine you ssh into a server and run the script from a different folder. `__file__` is always the absolute path to *this file* (`src/db.py`), regardless of where you ran the script from.

- `os.path.abspath(__file__)` → `/Users/you/.../RAG/src/db.py`
- `os.path.dirname(...)` → `/Users/you/.../RAG/src/`
- `os.path.dirname(...)` again → `/Users/you/.../RAG/`  ← project root

Then `os.path.join(BASE_DIR, 'data', 'podcasts.db')` builds the full path using the correct separator for your OS (`/` on Mac, `\` on Windows).

### Lines 10–17: `get_connection()`

```python
def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

- `os.makedirs(..., exist_ok=True)` — 🟢 Built-in. Creates the `data/` folder if it doesn't exist. `exist_ok=True` means "don't crash if it already exists."
- `sqlite3.connect(DB_PATH)` — 🔵 Library. Opens (or creates) the `.db` file. Returns a `conn` object — your "door" to the database.
- `conn.row_factory = sqlite3.Row` — 🔵 Library. Without this, each row comes back as an anonymous tuple: `(0, "Sam Altman")`. With `sqlite3.Row`, it becomes dict-like: `row['id']`, `row['title']`. Much more readable.

### Lines 25–91: `init_db()` — Table Creation

```python
cursor.execute("PRAGMA foreign_keys = ON;")
```

- 🔵 Library method. SQLite ignores foreign key constraints by default (for speed). This line turns enforcement on so we can't accidentally insert an orphaned chunk with a nonexistent `video_id`.

```python
cursor.execute("""
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    status TEXT DEFAULT 'new' CHECK(status IN ('new', 'processed', 'error'))
);
""")
```

- `CREATE TABLE IF NOT EXISTS` — SQL syntax (not Python). The `IF NOT EXISTS` means you can run this 100 times safely — it only creates the table the first time.
- `DEFAULT 'new'` — If you insert a row without specifying status, SQLite automatically sets it to `'new'`.
- `CHECK(status IN ('new', 'processed', 'error'))` — SQLite will reject any status value outside this list. Acts like a validation rule baked into the database.

### Lines 93–94: Saving and Closing

```python
conn.commit()
conn.close()
```

- `.commit()` — 🔵 Library. Writes all pending changes permanently to disk. Without this, your `INSERT` statements are lost when the script ends.
- `.close()` — 🔵 Library. Releases the file handle. Important to avoid file locking issues.

### Line 97–98: Entry Point

```python
if __name__ == "__main__":
    init_db()
```

⚙️ **Concept:** `__name__` is a special Python variable. When you run `python src/db.py` directly, `__name__` equals `"__main__"`. When another file does `from src.db import get_connection`, `__name__` equals `"src.db"`. So this block only runs when the file is the entry point, not when imported.

---

## File 2: `src/scraper.py` — Getting Video IDs from YouTube

**Role:** Reads channel URLs from `config/channels.yaml`, fetches video IDs and titles, inserts new ones into the `videos` table.

### Lines 1–10: Imports

```python
import scrapetube          # 🔵 Library — scrapes YouTube channel pages
import time                # 🟢 Built-in — lets us sleep between requests
import yaml                # 🔵 Library — reads .yaml config files
from datetime import datetime  # 🟢 Built-in — current date/time
```

- **`scrapetube`** — Scrolls through a YouTube channel page and streams back video metadata without needing the official YouTube API.
- **`yaml`** — YAML is a human-friendly config format. `yaml.safe_load(f)` parses it into a Python dict.
- **`datetime`** — `datetime.now().strftime("%Y-%m-%d")` produces a string like `"2026-02-19"`.

### Lines 12–17: `load_channels()`

```python
def load_channels():
    config_path = os.path.join(..., 'config', 'channels.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['channels']
```

- `with open(config_path, 'r') as f:` — 🟢 Built-in. Opens the file for reading. The `with` keyword guarantees the file is closed even if an error occurs — like a `try/finally` but cleaner.
- `yaml.safe_load(f)` — 🔵 Library. Parses the YAML text into a Python dict. `safe_load` (not `load`) prevents YAML from executing arbitrary code — a security best practice.
- `config['channels']` — 🟢 Dict key access. Returns the list of channel dicts.

### Lines 19–26: `get_existing_video_ids()`

```python
existing = {row['id'] for row in cursor.fetchall()}
```

⚙️ **Concept — Set Comprehension:**  
This is like a list comprehension, but it creates a **set** (curly braces). Sets hold unique values and have O(1) lookup time. `"abc123" in existing` is instant regardless of whether there are 10 or 10,000 videos. A list would be O(n) — slower with scale.

### Lines 28–54: `fetch_videos_for_channel()`

```python
videos = scrapetube.get_channel(channel_url=channel_url)
```
- 🔵 Library. Returns a Python **generator** — not a list. It streams videos one at a time (YouTube loads them lazily in batches). Memory-efficient for channels with 1000+ videos.

```python
video_id = video['videoId']
title    = video['title']['runs'][0]['text']
```
- `scrapetube` gives back raw YouTube JSON. `video['title']['runs'][0]['text']` is navigating nested dicts to get the readable title string. Purely 🟢 built-in dict/list access.

### Lines 56–90: `access_safe_scrape()`

```python
for channel in channels:
    found_videos = fetch_videos_for_channel(channel['url'], limit=limit)
    for vid in found_videos:
        if vid['id'] not in existing_ids:
            cursor.execute("INSERT INTO videos ...")
            existing_ids.add(vid['id'])
```

- `existing_ids.add(vid['id'])` — 🟢 Built-in set method. Adds the new ID to the in-memory set immediately, so if the same video appears twice in this run, we don't try to insert it twice.
- `time.sleep(1)` — 🟢 Built-in. Pauses the script for 1 second between channels. Without this, rapid requests get you rate-limited or blocked by YouTube.

---

## File 3: `src/transcripts.py` — Downloading the Transcript Text

**Role:** For every video marked `status = 'new'` in the DB, downloads the transcript from YouTube and stores the full text.

### Lines 5: Import

```python
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
```

- 🔵 Library. We import three things:
  - `YouTubeTranscriptApi` — the main class with `.fetch()` method
  - `TranscriptsDisabled` — an exception class for videos with no captions
  - `NoTranscriptFound` — an exception class for videos missing English captions

### Lines 20–57: `fetch_transcript(video_id)`

```python
api = YouTubeTranscriptApi()
transcript_obj = api.fetch(video_id)
```
- `YouTubeTranscriptApi()` — 🔵 creates an instance of the class.
- `.fetch(video_id)` — 🔵 Library method. Makes an HTTP request to YouTube's caption server and returns a `FetchedTranscript` object.

```python
if hasattr(transcript_obj, 'to_raw_data'):
    raw_data = transcript_obj.to_raw_data()
```

- `hasattr(obj, 'method_name')` — 🟢 Built-in. Returns `True` if the object has that method. We use this because `youtube_transcript_api` changed its return type across versions. This makes our code compatible with multiple versions.
- `.to_raw_data()` — 🔵 Library method. Converts the object into a plain Python list of dicts: `[{'text': '...', 'start': 10.5, 'duration': 2.3}, ...]`

```python
full_text = " ".join([item['text'] for item in raw_data])
```
- `" ".join([...])` — 🟢 Built-in. Takes a list of strings and joins them with a space separator. Result: one long string of the entire spoken transcript.

### Lines 59–62: Specific Exception Handling

```python
except (TranscriptsDisabled, NoTranscriptFound) as e:
    raise Exception(f"Transcripts disabled or not found: {e}")
```

⚙️ **Concept:** We catch *specific* exceptions (captions are off, or English isn't available) and re-raise a cleaner error. The outer loop in `process_video_transcripts` catches this, marks the video as `error`, and moves on — without crashing the whole pipeline.

### Lines 90–101: Status Updates

```python
cursor.execute("INSERT OR REPLACE INTO transcripts (video_id, full_text, raw_json) VALUES (?, ?, ?)",
               (video_id, full_text, json.dumps(raw_data)))
cursor.execute("UPDATE videos SET status = 'processed' WHERE id = ?", (video_id,))
```

- `INSERT OR REPLACE` — SQL. If this `video_id` already exists in the table, update it. If not, insert new.
- `json.dumps(raw_data)` — 🟢 Built-in. Converts the list of dicts into a JSON string for storage. We preserve the original timestamps even though we also store `full_text`.

---

## File 4: `src/ingest.py` — The Pipeline Orchestrator

**Role:** A single script that runs all three ingestion steps in order: Scrape → Transcripts → Metadata.

### Lines 1–2: Imports

```python
import argparse   # 🟢 Built-in — parses command-line arguments
```

### Lines 13–17: Argument Parsing

```python
parser = argparse.ArgumentParser(description="...")
parser.add_argument("--limit", type=int, default=None)
parser.add_argument("--step", type=str, choices=['all', 'scrape', 'transcript', 'metadata'], default='all')
args = parser.parse_args()
```

- `argparse.ArgumentParser()` — 🟢 Built-in class. Creates a parser that reads `sys.argv` (the command-line arguments you typed).
- `.add_argument("--limit", type=int)` — defines a flag. When you type `python main.py ingest --limit 50`, `args.limit` becomes the integer `50`.
- `choices=['all', 'scrape', ...]` — argparse automatically rejects any value not in this list and prints an error.

### Lines 22–36: Conditional Step Execution

```python
if args.step in ['all', 'scrape']:
    access_safe_scrape(limit=limit)
```

- `args.step in ['all', 'scrape']` — 🟢 Built-in `in` operator. Checks if the value is one of those two. Equivalent to `args.step == 'all' or args.step == 'scrape'` but cleaner.

---

## File 5: `src/metadata.py` — AI-Powered Entity + Relationship Extraction

**Role:** For each transcript without metadata yet, calls the Moonshot AI API (Kimi model) to extract guests, topics, companies, and typed relationship triples.

### Lines 1–7: Imports

```python
import json        # 🟢 Built-in
import time        # 🟢 Built-in
from openai import OpenAI       # 🔵 Library — OpenAI-compatible HTTP client
from dotenv import load_dotenv  # 🔵 Library — reads .env file
```

- **`openai` library** — We use this to talk to Moonshot AI because Moonshot's API is fully compatible with OpenAI's format. We just change the `base_url`.

### Lines 13–27: Allowed Verbs Taxonomy

```python
ALLOWED_VERBS = [
    "works_at", "founded", "co_founded", "left", "advises",
    "mentors", "criticizes", "collaborated_with", "disagrees_with",
    "advocates_for", "warns_against", "researches",
    "primarily_covers", "briefly_mentions"
]
```

- 🟠 Our code. This is the tiered constraint strategy. By defining exactly 15 verbs, we force the LLM to map any relationship it finds to one of these. Later, a safety filter strips any that slipped through.

### Lines 29–35: `get_moonshot_client()`

```python
return OpenAI(
    api_key=api_key,
    base_url="https://api.moonshot.ai/v1"
)
```

- `OpenAI(...)` — 🔵 Library class constructor. Normally points at `api.openai.com`. By passing `base_url`, we redirect it to Moonshot's servers. The rest of the SDK works identically.

### Lines 37–97: `extract_metadata(text)`

```python
truncated_text = text[:25000]
```
- `text[:25000]` — 🟢 Python slice. Takes the first 25,000 characters. The Moonshot 32k model can handle ~32,000 *tokens* (~120,000 chars), but 25,000 chars is a safe budget.

```python
allowed_verbs_str = ", ".join(ALLOWED_VERBS)
```
- 🟢 Built-in. Joins our list into a comma-separated string to embed in the prompt.

```python
completion = client.chat.completions.create(
    model="moonshot-v1-32k",
    messages=[...],
    temperature=0.2
)
```
- `.chat.completions.create(...)` — 🔵 Library method. Sends the HTTP request to the LLM API. `temperature=0.2` makes output more deterministic (less creative, more consistent JSON).

```python
content = completion.choices[0].message.content
```
- 🔵 Library attribute chain. The API returns a response object. `.choices[0]` is the first (and only) response. `.message.content` is the string the model generated.

```python
if content.startswith("```json"):
    content = content.replace("```json", "").replace("```", "").strip()
```
- `.startswith(...)` — 🟢 Built-in string method. Checks if the string begins with this sequence.
- `.replace(...)` — 🟢 Built-in. Removes markdown code fences the LLM sometimes adds.
- `.strip()` — 🟢 Built-in. Removes leading/trailing whitespace.

```python
data = json.loads(content)
```
- `json.loads(...)` — 🟢 Built-in. Parses a JSON string into a Python dict. This is the inverse of `json.dumps()`.

```python
data["relationships"] = [
    r for r in data["relationships"]
    if isinstance(r, dict) and r.get("verb") in ALLOWED_VERBS
]
```
- Safety filter: even if the LLM hallucinated a verb like `"competed_with"`, this list comprehension removes it.
- `isinstance(r, dict)` — 🟢 Built-in. Checks the type of `r`.
- `.get("verb")` — 🟢 Built-in dict method. `dict.get(key)` returns `None` if the key is missing, instead of crashing.

---

## File 6: `src/chunking.py` — Splitting Transcripts

**Role:** Breaks a full transcript into large "Parent" chunks and small "Child" chunks. Children are searched; Parents are retrieved for context.

### Lines 1: Import

```python
import uuid   # 🟢 Built-in — generates unique IDs
```

- `uuid.uuid4()` generates a random 128-bit ID like `"3f2504e0-4f89-11d3-9a0c-0305e82c3301"`. Guaranteed unique.

### Lines 3–42: `chunk_text(text, chunk_size, overlap)`

```python
while start < text_len:
    end = min(start + chunk_size, text_len)
```

- `min(a, b)` — 🟢 Built-in. Returns the smaller of two numbers. This prevents us from indexing past the end of the string.

```python
    last_space = chunk_text.rfind(' ')
    if last_space != -1 and last_space > chunk_size * 0.5:
        end = start + last_space + 1
```

- `.rfind(' ')` — 🟢 Built-in string method. Searches for the last occurrence of a space, scanning from the right. Returns the index, or -1 if not found.

⚙️ **Example:** Chunk would end at character 1000, which cuts "superintelligence" mid-word:  
`"...the future of superintellig|ence and how"`  
`rfind(' ')` finds the space before "superintelligence", so we end there instead:  
`"...the future of |superintelligence and how"`

```python
    start += (chunk_size - overlap)
```
- Each loop iteration advances `start` by `chunk_size - overlap`. If overlap is 100, we move forward 900 chars. The next chunk starts 100 chars before where the previous ended — creating purposeful repetition to avoid losing context at boundaries.

### Lines 44–102: `create_parent_child_chunks(video_id, full_text)`

```python
parent_id = str(uuid.uuid4())
```
- `uuid.uuid4()` — 🟢 Built-in. Generates a UUID object. `str(...)` converts it to a string.

```python
all_chunks.append({
    'id': parent_id,
    'video_id': video_id,
    'type': 'parent',
    'parent_id': None,
    ...
})
```

Then for each parent, we chunk its text into children:
```python
child_chunks_data = chunk_text(p_data['text'], chunk_size=1000, overlap=100)
for c_data in child_chunks_data:
    all_chunks.append({
        'type': 'child',
        'parent_id': parent_id,   # ← link to its parent
        ...
    })
```

⚙️ **Why nest the chunking?** We chunk the text into 3000-char Parents first, then re-chunk each Parent into 1000-char Children. This guarantees every child is a strict subset of exactly one parent — no child spans two parents.

---

## File 7: `src/embeddings.py` — Converting Text to Vectors

**Role:** Manages the embedding model and ChromaDB vector database. Converts child chunk text into numeric vectors and stores them.

### Lines 3–5: Imports

```python
import chromadb                                      # 🔵 Library — vector database
from chromadb.config import Settings                  # 🔵 Library — config class
from sentence_transformers import SentenceTransformer # 🔵 Library — embedding model
```

### Lines 17–26: `get_chroma_client()` — Singleton Pattern

```python
_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH, settings=Settings(allow_reset=True))
    return _chroma_client
```

⚙️ **Concept — Singleton:**  
`global _chroma_client` means we're referencing the module-level variable, not creating a local one.  
The `if None` check means we only create the client once per Python session. If you call `get_chroma_client()` 50 times across different functions, it only opens the database file once. Like a shared "door" to the DB.

- `chromadb.PersistentClient(path=...)` — 🔵 Library. Creates a client that reads/writes the `.chroma_db/` folder on disk. Data survives restarts.
- `Settings(allow_reset=True)` — 🔵 Library config class. Allows `client.reset()` to wipe data in testing.

### Lines 28–32: `get_embedding_model()` — Lazy Loading

```python
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _embedding_model
```

- `SentenceTransformer("all-MiniLM-L6-v2")` — 🔵 Library. Downloads (first time) or loads a 384-dimension text embedding model. Loading takes ~2 seconds. By caching in `_embedding_model`, we only pay this cost once.

### Lines 39–83: `embed_and_store(chunks)`

```python
child_chunks = [c for c in chunks if c['type'] == 'child']
```
- 🟢 List comprehension. Filters the mixed list of parent and child chunks. We only embed children — parents are stored in SQLite for retrieval later.

```python
embeddings = model.encode(documents).tolist()
```
- `model.encode(documents)` — 🔵 Library. Takes a list of strings, feeds them through the neural network, returns a 2D numpy array of shape `(50, 384)` — one 384-float vector per document.
- `.tolist()` — 🔵 Numpy method. Converts to a plain Python list of lists, which ChromaDB requires.

```python
collection.upsert(
    ids=ids,
    embeddings=embeddings,
    documents=documents,
    metadatas=metadatas
)
```
- `.upsert(...)` — 🔵 ChromaDB method. "Update or Insert." If an ID exists, updates it. If new, inserts. Safe to call repeatedly without creating duplicates.

---

## File 8: `src/backfill.py` — Processing Existing Transcripts

**Role:** Finds transcripts already in SQLite that haven't been chunked/embedded yet, and runs them through `chunking.py` and `embeddings.py`.

### The Key Query

```python
cursor.execute("""
    SELECT t.video_id, t.full_text 
    FROM transcripts t
    WHERE t.video_id NOT IN (SELECT DISTINCT video_id FROM chunks)
""")
```

⚙️ **Why `NOT IN (...)`?** This is the idempotency guarantee. It asks: "Who is in `transcripts` but not yet in `chunks`?" If the script crashes midway, the next run sees the already-completed videos in `chunks` and skips them automatically. You can run `backfill.py` a hundred times safely.

```python
chunks = create_parent_child_chunks(video_id, full_text)
```
- 🟠 Our code from `chunking.py`. Returns a list of up to 300 chunk dicts.

```python
for c in chunks:
    cursor.execute("INSERT INTO chunks (id, ...) VALUES (?, ...)", (c['id'], ...))
```
- Stores all chunks (both parents and children) in SQLite.

```python
embed_and_store(chunks)
```
- 🟠 Our code from `embeddings.py`. This internally filters for children only, encodes, and upserts into ChromaDB.

```python
conn.commit()
```
- Written after BOTH the SQLite write and ChromaDB write succeed. If `embed_and_store` throws an error, `commit()` is never called, so the SQLite data is also rolled back via `conn.rollback()`. Keeps both stores in sync.

---

## File 9: `src/retrieval.py` — The Hybrid Search Engine

**Role:** The core of the RAG system. Takes a user's question and finds the most relevant podcast passages using 4 stages: BM25 (keyword) → Vector → RRF Fusion → Cohere Rerank → Parent Context.

### The `__init__` — Empty Workshop Pattern

```python
def __init__(self):
    self._bm25_index  = None   # Empty shelf
    self._bm25_corpus = None   # Empty shelf
    self._cohere_client = None # Empty shelf
```

⚙️ **Think of it like this:**  
You're setting up a search service. `__init__` opens the office door — the room is empty. The tools (BM25 index, Cohere connection) aren't deployed until you explicitly call `build_bm25_index()`. This is "lazy initialization" — you only unpack the tools when you need them. Creating the object is instant; building the index takes time.

### `build_bm25_index()`

```python
self._bm25_corpus = [
    {'id': r['id'], 'tokens': r['text'].lower().split()}
    for r in rows
]
```

**Example:** One row from the database:
```
id: "abc-123"
text: "Sam Altman discussed the AGI timeline with Lex"
```
Becomes:
```python
{'id': 'abc-123', 'tokens': ['sam', 'altman', 'discussed', 'the', 'agi', 'timeline', 'with', 'lex']}
```

- `.lower()` — normalizes case so "AGI" and "agi" match the same query.
- `.split()` — splits on whitespace. Simple but effective for BM25.

```python
self._bm25_index = BM25Okapi(tokenized)
```

⚙️ **What BM25 does internally:**  
It calculates, for every word: "How often does this word appear in this chunk?" and "How rare is this word across ALL chunks?" Rare words that appear often in a chunk → high signal. Common words like "the" → low signal. This pre-computation is what makes `.get_scores()` instant at query time.

### `search_vector()`

```python
query_embedding = model.encode([query]).tolist()[0]
results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
scores = [1 / (1 + d) for d in results['distances'][0]]
```

- ChromaDB returns **L2 distance** — lower = more similar. `1 / (1 + d)` converts to a 0–1 similarity score where higher = more relevant.
- **Example:** Distance 0.0 (identical) → score `1.0`. Distance 1.0 (somewhat different) → score `0.5`. Distance 9.0 (very different) → score `0.1`.

### `rrf_fusion()` — Reciprocal Rank Fusion

```python
for rank, item in enumerate(bm25_results):
    scores[item['id']] = scores.get(item['id'], 0.0) + 1.0 / (k + rank + 1)
```

⚙️ **The problem it solves:**  
BM25 scores are on a scale of 0–10. Vector scores are on a scale of 0–1. You can't add them directly — it would unfairly weight BM25. RRF ignores the raw score and only uses rank position.

**Example:**
- BM25 ranks chunk "abc" at position 1 → `1/(60+1) = 0.0164`
- Vector ranks chunk "abc" at position 3 → `1/(60+3) = 0.0159`
- Combined RRF score: `0.0164 + 0.0159 = 0.0323`
- A chunk that appears in only one list scores at most `0.0164`.

Chunks that both methods agree on float to the top.

### `rerank()`

```python
co = cohere.ClientV2(api_key=api_key)
response = co.rerank(model="rerank-v3.5", query=query, documents=documents, top_n=top_n)
```

- `cohere.ClientV2(...)` — 🔵 Library constructor. Opens an HTTPS connection to Cohere's API.
- `.rerank(...)` — 🔵 Library method. Sends all candidate texts + query to a cross-encoder model. Unlike BM25 or vectors (which encode query and document separately), a cross-encoder reads them together for much higher accuracy.

```python
for result in response.results:
    original_idx = result.index
    chunk_id = chunk_ids[original_idx]
```
- `result.index` — 🔵 Library attribute. Cohere returns results in a new order but references the **original position** in the list you sent. `chunk_ids[original_idx]` recovers the actual chunk ID.

### `get_context()`

```python
parent_ids = list({r['parent_id'] for r in child_rows.values() if r['parent_id']})
```
- `{...}` — 🟢 Set comprehension. Collects unique parent IDs (a child found twice for the same parent shouldn't fetch the parent twice).
- `list(...)` — 🟢 Built-in. Converts the set to a list for the SQL `IN ()` query.

```python
'parent_text': parent_row.get('text', res['text'])
```
- `dict.get(key, default)` — 🟢 Built-in. If the parent isn't found (edge case), fallback to the child's text instead of crashing.

---

## File 10: `src/query.py` — The LLM Answer Generator

**Role:** Takes a user question, calls `retrieval.py` to get context, formats it, sends to Moonshot AI, and streams the answer with citations.

### Singleton Retriever

```python
_retriever = None

def get_retriever():
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever()
        _retriever.build_bm25_index()
    return _retriever
```

⚙️ **Why?** Building the BM25 index takes ~0.5 seconds and reads the full DB. If you run 10 queries in one session, you don't want to rebuild it 10 times. The singleton pattern: build once, reuse everywhere.

### `_build_context_block()`

```python
for i, c in enumerate(context_results, start=1):
    sources.append({'index': i, 'video_id': video_id, 'title': title})
    blocks.append(f"[Source {i}: {title}]\n{c['parent_text']}")

return "\n\n---\n\n".join(blocks), sources
```

- `enumerate(..., start=1)` — 🟢 Built-in. Loops with index starting at 1 (not 0), so citations read `[Source 1]` naturally.
- `f"[Source {i}: {title}]"` — 🟢 Python f-string. Injects variables directly into a string.
- `"\n\n---\n\n".join(blocks)` — 🟢 Built-in. Joins all context blocks with a horizontal rule separator to make it legible in the prompt.

### System Prompt

```python
SYSTEM_PROMPT = """You are an expert research assistant...
Answer STRICTLY using the provided context. Do not use outside knowledge.
For every claim, cite the source using [Source N] notation."""
```

This is 🟠 our design. The LLM has no memory between calls. The entire "personality" and rules are injected fresh every query via this system prompt.

### Streaming the Response

```python
response = client.chat.completions.create(..., stream=True)

for chunk in response:
    delta = chunk.choices[0].delta.content or ""
    print(delta, end="", flush=True)
```

- `stream=True` — 🔵 Library parameter. Instead of waiting for the full response (could be 5+ seconds), the API sends tokens as they're generated.
- `print(delta, end="", flush=True)` — `end=""` prevents a newline after each token. `flush=True` forces immediate output to the terminal instead of buffering.

---

## The Big Picture: How All Files Connect

```
channels.yaml
     ↓
scraper.py       → videos table (SQLite)
     ↓
transcripts.py   → transcripts table (SQLite)
     ↓
metadata.py      → metadata + relationships tables (SQLite)
     ↓
chunking.py      → list of chunk dicts (in memory)
     ↓
backfill.py  ─── → chunks table (SQLite) + ChromaDB (vectors)
                         ↓                    ↓
                    retrieval.py ──── builds BM25 from chunks
                                 ──── queries ChromaDB
                                 ──── calls Cohere rerank
                                 ──── fetches parents from chunks table
                         ↓
                    query.py ────── formats context
                                ──── calls Moonshot AI
                                ──── streams answer with [Source N] citations
```

Every file is a single layer of responsibility. None of them know about the others except through the explicit imports at the top.
