"""
Pinecone Vector Store & Retrieval Engine with Local Persistence.

Indexes contract text embeddings via OpenRouter (nvidia/llama-nemotron-embed-vl-1b-v2:free),
supports Pinecone Cloud Vector Store, cosine similarity search, and persistent storage.
"""

import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI

from app.config import AppConfig, setup_logger

logger = setup_logger("vector_store")

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two vector embeddings."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot / (norm_v1 * norm_v2)


class VectorStoreManager:
    """
    Manages indexing and similarity search for contract chunks using OpenRouter embeddings.
    Supports Pinecone Cloud Vector Store with local persistent index fallback.
    """

    def __init__(self):
        self.use_pinecone = False
        self.pinecone_index = None
        self.local_store_path: Path = AppConfig.LOCAL_VECTOR_STORE_PATH
        self.chunks_db: List[Dict[str, Any]] = []

        self._init_client()

    def _init_client(self):
        """Attempts to initialize Pinecone API client; falls back to local vector store."""
        api_key = AppConfig.PINECONE_API_KEY
        index_name = AppConfig.PINECONE_INDEX_NAME

        if api_key and api_key != "your_pinecone_api_key":
            try:
                from pinecone import Pinecone, ServerlessSpec
                pc = Pinecone(api_key=api_key)
                
                # Check existing indexes
                existing_indexes = [idx.name for idx in pc.list_indexes()]
                if index_name not in existing_indexes:
                    logger.info(f"Creating Pinecone index '{index_name}' with dimension {AppConfig.EMBEDDING_DIMENSION}...")
                    pc.create_index(
                        name=index_name,
                        dimension=AppConfig.EMBEDDING_DIMENSION,  # 2048 for nvidia/llama-nemotron-embed-vl-1b-v2:free
                        metric="cosine",
                        spec=ServerlessSpec(cloud="aws", region="us-east-1")
                    )
                self.pinecone_index = pc.Index(index_name)
                self.use_pinecone = True
                logger.info(f"Pinecone Vector Store initialized successfully (index: {index_name}).")
                return
            except Exception as e:
                logger.warning(f"Could not connect to Pinecone ({e}). Falling back to local vector store.")
        
        logger.info(f"Using Local Persistent Vector Store at {self.local_store_path}")
        self._load_local_store()

    def _load_local_store(self):
        """Loads locally persisted chunk embeddings from disk."""
        if self.local_store_path.exists():
            try:
                with open(self.local_store_path, "r", encoding="utf-8") as f:
                    self.chunks_db = json.load(f)
                logger.info(f"Loaded {len(self.chunks_db)} contract chunks from local vector store.")
            except Exception as e:
                logger.error(f"Error loading local vector store: {e}")
                self.chunks_db = []
        else:
            self.chunks_db = []

    def _save_local_store(self):
        """Saves current chunk embeddings database to disk."""
        self.local_store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.local_store_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks_db, f, indent=2, ensure_ascii=False)

    def generate_embeddings(self, texts: List[str], client: OpenAI) -> List[List[float]]:
        """
        Generates vector embeddings for text chunks using OpenRouter Embedding API
        (nvidia/llama-nemotron-embed-vl-1b-v2:free).
        """
        if not AppConfig.OPENROUTER_API_KEY or AppConfig.OPENROUTER_API_KEY.startswith("your_"):
            # Test fallback for unconfigured API key during offline local development
            logger.warning("OPENROUTER_API_KEY is not configured in .env. Generating local mock embeddings for testing.")
            embeddings = []
            dim = AppConfig.EMBEDDING_DIMENSION
            for text in texts:
                val = sum(ord(c) for c in text) % 1000 / 1000.0
                vec = [math.sin(i + val) for i in range(dim)]
                norm = math.sqrt(sum(v*v for v in vec))
                embeddings.append([v / norm for v in vec])
            return embeddings

        try:
            response = client.embeddings.create(
                model=AppConfig.EMBEDDING_MODEL,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.warning(f"OpenRouter Embedding API call failed ({e}). Falling back to local vector generation.")
            embeddings = []
            dim = AppConfig.EMBEDDING_DIMENSION
            for text in texts:
                val = sum(ord(c) for c in text) % 1000 / 1000.0
                vec = [math.sin(i + val) for i in range(dim)]
                norm = math.sqrt(sum(v*v for v in vec))
                embeddings.append([v / norm for v in vec])
            return embeddings

    def add_contract_chunks(self, chunks: List[Dict[str, Any]], client: OpenAI) -> int:
        """
        Embeds and indexes a list of contract chunks.
        Each chunk is a dict with keys: 'chunk_id', 'text', 'metadata'.
        """
        if not chunks:
            return 0

        texts = [c["text"] for c in chunks]
        embeddings = self.generate_embeddings(texts, client)

        records_to_upsert = []
        for chunk, embedding in zip(chunks, embeddings):
            record = {
                "id": chunk["chunk_id"],
                "text": chunk["text"],
                "metadata": chunk.get("metadata", {}),
                "embedding": embedding
            }
            records_to_upsert.append(record)

        if self.use_pinecone and self.pinecone_index:
            try:
                pinecone_vectors = [
                    (r["id"], r["embedding"], {**r["metadata"], "text": r["text"]})
                    for r in records_to_upsert
                ]
                batch_size = 100
                for i in range(0, len(pinecone_vectors), batch_size):
                    self.pinecone_index.upsert(vectors=pinecone_vectors[i:i+batch_size])
                logger.info(f"Upserted {len(records_to_upsert)} chunks to Pinecone index.")
            except Exception as e:
                logger.error(f"Failed to upsert to Pinecone: {e}. Indexing locally.")
                self.chunks_db.extend(records_to_upsert)
                self._save_local_store()
        else:
            existing_ids = {c["id"] for c in self.chunks_db}
            for record in records_to_upsert:
                if record["id"] in existing_ids:
                    self.chunks_db = [c for c in self.chunks_db if c["id"] != record["id"]]
                self.chunks_db.append(record)
            self._save_local_store()
            logger.info(f"Indexed {len(records_to_upsert)} chunks into local vector store.")

        return len(records_to_upsert)

    def search_similar_chunks(
        self,
        query: str,
        client: OpenAI,
        k: int = 4,
        score_threshold: float = 0.0,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes vector similarity search against Pinecone or local vector store.
        Returns top-k matching chunks with similarity score and metadata.
        """
        query_embedding = self.generate_embeddings([query], client)[0]

        if self.use_pinecone and self.pinecone_index:
            try:
                query_args = {
                    "vector": query_embedding,
                    "top_k": k,
                    "include_metadata": True
                }
                if metadata_filter:
                    query_args["filter"] = metadata_filter

                response = self.pinecone_index.query(**query_args)
                results = []
                for match in response.matches:
                    score = float(match.score)
                    if score >= score_threshold:
                        meta = dict(match.metadata)
                        text = meta.pop("text", "")
                        results.append({
                            "chunk_id": match.id,
                            "text": text,
                            "similarity_score": score,
                            "metadata": meta
                        })
                return results
            except Exception as e:
                logger.error(f"Pinecone search error: {e}. Falling back to local vector search.")

        # Local Vector Search
        results = []
        for chunk in self.chunks_db:
            if metadata_filter:
                match_filter = True
                chunk_meta = chunk.get("metadata", {})
                for fk, fv in metadata_filter.items():
                    if chunk_meta.get(fk) != fv:
                        match_filter = False
                        break
                if not match_filter:
                    continue

            score = cosine_similarity(query_embedding, chunk["embedding"])
            if score >= score_threshold:
                results.append({
                    "chunk_id": chunk["id"],
                    "text": chunk["text"],
                    "similarity_score": score,
                    "metadata": chunk.get("metadata", {})
                })

        results.sort(key=lambda x: x["similarity_score"], reverse=True)
        return results[:k]

    def list_indexed_contracts(self) -> List[Dict[str, Any]]:
        """Returns unique corporate contracts currently stored in the vector index."""
        contracts_map = {}
        for chunk in self.chunks_db:
            meta = chunk.get("metadata", {})
            cid = meta.get("contract_id") or meta.get("document_id") or "unknown"
            if cid not in contracts_map:
                contracts_map[cid] = {
                    "contract_id": cid,
                    "title": meta.get("contract_title") or meta.get("filename") or cid,
                    "contract_type": meta.get("contract_type", "General Contract"),
                    "total_chunks": 0,
                    "upload_date": meta.get("ingested_at", "N/A")
                }
            contracts_map[cid]["total_chunks"] += 1

        return list(contracts_map.values())

    def delete_contract(self, contract_id: str) -> bool:
        """Deletes all vector chunks belonging to a specific contract ID."""
        if self.use_pinecone and self.pinecone_index:
            try:
                self.pinecone_index.delete(filter={"contract_id": contract_id})
            except Exception as e:
                logger.error(f"Pinecone delete error: {e}")

        initial_len = len(self.chunks_db)
        self.chunks_db = [
            c for c in self.chunks_db
            if c.get("metadata", {}).get("contract_id") != contract_id and
               c.get("metadata", {}).get("document_id") != contract_id
        ]
        self._save_local_store()
        return len(self.chunks_db) < initial_len

vector_store = VectorStoreManager()
