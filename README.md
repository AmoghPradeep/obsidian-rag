# Obsidian RAG MCP

Turn an Obsidian vault into a long-term memory system for LLM agents.

This project helps capture knowledge from voice notes, PDFs, and handwritten material, convert it into clean markdown, and make it retrievable through MCP. The result is a memory layer an agent can keep querying over time instead of starting from zero every session.

## What It Lets You Do

- Capture voice notes and turn them into structured Obsidian notes automatically.
- Convert PDFs, scans, and handwritten documents into searchable knowledge.
- Build a semantic memory store over your vault so agents can retrieve relevant context on demand.
- Let an MCP-connected agent update notes with refreshed summaries and tags without rewriting the original content.
- Keep knowledge in your own files instead of trapping it inside chat logs or a proprietary app.

## Why This Exists

Most useful personal knowledge is messy at the source:

- spoken thoughts
- meeting recordings
- handwritten pages
- exported documents
- half-finished markdown notes

LLM agents are good at using knowledge, but bad at remembering it unless that knowledge is captured, normalized, and indexed somewhere durable.

Obsidian RAG MCP is built to close that gap. It gives you a way to continuously turn raw personal knowledge into an agent-readable memory base.

## How It Works

At a high level, the system has two jobs:

1. A background worker watches for new source material and turns it into clean markdown in your Obsidian vault.
2. An MCP server lets agents query that memory store or update existing notes safely.

The flow looks like this:

`raw input -> normalized note -> chunking + embeddings -> searchable memory -> MCP access for agents`

Today, the main ingestion paths are:

- audio files such as voice notes
- PDF documents, including handwritten or scanned material when the extraction model can interpret them

## Core Experience

Imagine this workflow:

1. You drop a voice memo or document into a watched folder.
2. The system converts it into a readable markdown note in your vault.
3. That note is tagged, summarized, and indexed for retrieval.
4. Later, your LLM agent asks for relevant context through MCP.
5. The agent gets grounded memory from your vault instead of relying only on the current chat.

That is the core value of this project: persistent memory that compounds over time.

## Current Capabilities

- Background ingestion for audio and PDF sources
- Markdown normalization and vault-safe note creation
- Semantic retrieval over indexed vault content
- MCP tool support for context retrieval
- MCP tool support for safe note enrichment and reindexing

## In Progress

The next major step in OpenSpec is expanding ingestion beyond PDFs into folders of ordered page images, such as Apple Notes exports, while continuing the shift toward a Linux-first deployment model.

## Who This Is For

- people building personal knowledge systems around Obsidian
- developers experimenting with MCP-connected agents
- anyone who wants voice notes and handwritten material to become usable agent memory
- local-first users who want their knowledge stored in files they control

## Quick Start

Install the project:

```bash
python -m pip install -e .[test]
```

Start the background worker:

```bash
obsidian-rag-background
```

Start the MCP server:

```bash
obsidian-rag-mcp-server
```

Configuration is read from `OBRAG_` environment variables and `~/.obragconfig/.env`.

For operational setup and recovery details, see [docs/runbook.md](docs/runbook.md).

## Project Direction

This repository started as a way to make an Obsidian vault retrievable through MCP, then expanded into an always-on ingestion pipeline for turning raw personal knowledge into durable memory. The direction now is broader: make Obsidian a practical long-term memory backend for LLM agents, especially for knowledge that begins as speech, scans, or handwritten notes.
