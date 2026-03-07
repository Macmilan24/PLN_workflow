import os
import json
import numpy as np
import faiss
import re
from sentence_transformers import SentenceTransformer
from neo4j_client import Neo4jConnector
from config import Config


class VectorIndexer:
    def __init__(self, db: Neo4jConnector):
        self.db = db
        print("Loading Sentence Transformer ...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        # all-MiniLM-L6-v2 returns 384-dimensional embeddings.
        self.embeding_dim = 384

        self.rich_documents = []
        self.node_symbols = []

    def _clean_symbol(self, val: str) -> str:
        if not val:
            return "Unknown"

        s = str(val).strip()
        if not s:
            return "Unknown"

        # Normalize free-text names into stable MeTTa-safe symbol tokens.
        s = s.replace('"', "").replace("'", "")
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^A-Za-z0-9_]", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")

        if not s:
            return "Unknown"
        if s[0].isdigit():
            s = f"S_{s}"
        return s

    def extract_node(self):

        query = """
        MATCH (n) 
        WHERE labels(n)[0] IN['Tool', 'Workflow', 'Category', 'Step']
        
        // Optional: Get inputs/outputs if it's a Tool
        OPTIONAL MATCH (n)-[:TOOL_HAS_INPUT]->(i)
        OPTIONAL MATCH (n)-[:TOOL_HAS_OUTPUT]->(o)
        
        RETURN 
            labels(n)[0] AS node_type, 
            coalesce(n.name, n.id, 'Unknown') AS node_name,
            coalesce(n.description, n.text, '') AS description,
            collect(DISTINCT coalesce(i.name, i.format, '')) AS inputs,
            collect(DISTINCT coalesce(o.name, o.format, '')) AS outputs
        """

        result = self.db.execute_read_query(query)

        for row in result:
            node_type = row["node_type"]
            raw_name = row["node_name"]
            dec = row["description"]

            # Build one rich text per node so embedding captures structure and semantics.
            context_text = [f"Type: {node_type}", f"Name: {raw_name}"]

            Inputs = [ip for ip in row["inputs"] if ip]
            Outputs = [op for op in row["outputs"] if op]

            if Inputs:
                context_text.append(f"Inputs: {", ".join(Inputs)}")
            if Outputs:
                context_text.append(f"Outputs: {", ".join(Outputs)}")
            if dec:
                context_text.append(f"Description: {dec}")

            rich_text = " | ".join(context_text)

            self.rich_documents.append(rich_text)
            # Keep a parallel FAISS-id -> symbol list for later retrieval.
            self.node_symbols.append(self._clean_symbol(raw_name))

        print(f"Extracted {len(self.rich_documents)} for the Latent Space")

    def build_and_save_index(self):
        print("Generating Embedding ...")

        # Encode all documents in one batch, then cast for FAISS compatibility.
        embeddings = self.model.encode(self.rich_documents, show_progress_bar=True)
        embeddings = np.array(embeddings).astype("float32")

        print("Building FAISS Index ...")

        # HNSW gives fast approximate nearest-neighbor search at scale.
        index = faiss.IndexHNSWFlat(self.embeding_dim, 32)

        # L2-normalized vectors make inner-product/L2 comparisons behave like cosine similarity.
        faiss.normalize_L2(embeddings)
        index.add(embeddings)

        os.makedirs(Config.VECTOR_OUTPUT_DIR, exist_ok=True)

        index_path = os.path.join(Config.VECTOR_OUTPUT_DIR, "galaxy_index.faiss")
        faiss.write_index(index, index_path)

        mapping_path = os.path.join(Config.VECTOR_OUTPUT_DIR, "faiss_mapping.json")
        # JSON keys become strings on write; loader in perception_engine handles that.
        mapping_dict = {i: symbol for i, symbol in enumerate(self.node_symbols)}

        with open(mapping_path, "w") as f:
            json.dump(mapping_dict, f, indent=2)

        print(f"Embedding saved {index_path}.")
