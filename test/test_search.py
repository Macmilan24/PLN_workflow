from pathlib import Path
import faiss
import json
from sentence_transformers import SentenceTransformer
import numpy as np


def test_search():

    model = SentenceTransformer("all-MiniLM-L6-v2")

    base_dir = Path(__file__).resolve().parents[1]
    index_path = base_dir / "vector_DB" / "galaxy_index.faiss"
    mapping_path = base_dir / "vector_DB" / "faiss_mapping.json"

    index = faiss.read_index(str(index_path))

    with open(mapping_path, "r") as f:
        mapping = json.load(f)

    print("System loaded.")
    print("-" * 30)

    user_query = "I need a tool to align human RNA-seq reads to a reference genome, and it should handle splice junctions."
    print(f"User Says = {user_query}")

    query_vector = model.encode([user_query])
    query_vector = np.array(query_vector).astype("float32")

    faiss.normalize_L2(query_vector)

    k = 15

    distances, indices = index.search(query_vector, k)

    print(f"FAISS found this top {k} Matchs:")

    for i in range(k):
        faiss_idx = str(indices[0][i])
        distance = distances[0][i]

        node_name = mapping.get(faiss_idx, "UNKNOWN_NODE")

        print(f"Rank {i + 1} | Distance: {distance:.4f} | Node: {node_name}")


if __name__ == "__main__":
    test_search()
