import chromadb
from pathlib import Path
from core.llm import GeminiClient, GeminiEmbeddingFunction

DB_DIR = Path(__file__).parent.parent / "data" / "chroma_db"

class SimpleRAG:
    def __init__(self, db_dir=DB_DIR):
        self.llm_client = GeminiClient()
        self.embedding_fn = GeminiEmbeddingFunction(self.llm_client)
        
        # Ensure db directory exists
        Path(db_dir).mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=str(db_dir))
        self.collection = self.client.get_or_create_collection(
            name="git_assist_docs",
            embedding_function=self.embedding_fn
        )

    def ingest(self, documents):
        """
        Ingests a list of documents into the vector database.
        documents: List of dicts {id, text, metadata}
        """
        if not documents:
            print("No documents to ingest.")
            return

        # Chroma expects lists
        ids = [d['id'] for d in documents]
        texts = [d['text'] for d in documents]
        metadatas = [d['metadata'] for d in documents]

        print(f"Upserting {len(documents)} chunks to Chroma...")
        try:
            self.collection.upsert(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )
            print("Ingestion complete.")
        except Exception as e:
            print(f"Error during ingestion: {e}")

    def retrieve(self, query, n_results=5, repo_filter=None):
        """
        Retrieves the most relevant documents for a given query.
        """
        where = {}
        if repo_filter:
            where["repo"] = repo_filter
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where if where else None
            )
            
            # Flatten results
            flattened = []
            if results['documents'] and results['documents'][0]:
                for i, text in enumerate(results['documents'][0]):
                    flattened.append({
                        "text": text,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "id": results['ids'][0][i]
                    })
            
            return flattened
        except Exception as e:
            print(f"Error during retrieval: {e}")
            return []
