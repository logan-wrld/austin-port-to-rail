# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Austin Port-to-Rail is a multimodal freight logistics optimization system that provides real-time insights into freight flow from port to truck to rail networks around the Port of Houston. It uses a RAG (Retrieval-Augmented Generation) architecture with local LLM to answer queries grounded in actual logistics data.

## Tech Stack

- **Backend**: Python with LangChain, ChromaDB (vector store), Ollama (local LLM - qwen2.5:1.5b)
- **Embeddings**: HuggingFace sentence-transformers (all-MiniLM-L6-v2)
- **Frontend**: Vanilla HTML/JS with Leaflet.js for mapping

## Common Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Index all CSV data into ChromaDB (run once or when data changes)
python indexing.py

# Start interactive query interface
python query.py

# Serve the map visualization
python3 -m http.server 8000
```

## Architecture

### Data Pipeline

1. **Indexing** (`indexing.py`): Loads CSVs from `data/`, converts to LangChain Documents, chunks text (500 chars, 50 overlap), generates embeddings, stores in ChromaDB at `./chroma/`

2. **Query** (`query.py`): Loads ChromaDB, retrieves k=4 similar documents, feeds context to Ollama LLM for grounded responses

3. **Visualization** (`port-of-houston-map.html`): Leaflet-based map showing Port of Houston with vessel tracking, terminals, and rail network layers

### Data Sources

- `data/portwatch-houston.csv` - Port activity from IMF PortWatch
- `data/railroad-lines.csv`, `data/railroad-nodes.csv` - Rail network from USDOT/FRA
- `data/truck-travel-times.csv` - County-to-county drayage times from BTS/ATRI
- `data/logistics-data-merged.csv` - Fleet-level freight metrics
- `data/texas_rail_data.csv` - Texas-specific rail data

## Key Implementation Details

- ChromaDB persists to `./chroma/` directory
- Batch inserts of 5000 documents for efficient indexing
- Uses Ollama for privacy-first local LLM inference (no cloud API calls)
- Documents include metadata: source file name and row index
