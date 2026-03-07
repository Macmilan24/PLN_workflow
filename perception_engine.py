import faiss
import json
from sentence_transformers import SentenceTransformer
import numpy as np


class PerceptionEngine:
    def __init__(
        self,
        index_path: str,
        mapping_path: str,
        top_k: int = 50,
        temprature: float = 0.15,
    ):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.read_index(index_path)

        with open(mapping_path, "r") as f:
            self.mapping = json.load(f)

        self.top_k = top_k
        self.temp = temprature

    def calculate_stv(self, distance: np.array):
        # For normalized vectors, squared L2 distance maps monotonically to cosine similarity.
        cosine_sim = 1.0 - (distance / 2.0)
        cosine_sim = np.clip(cosine_sim, 0.0, 1.0)

        # Confidence curve: low around weak matches, quickly rises for strong semantic matches.
        midpoint = 0.55
        steepness = 12.0

        confidences = 1.0 / (1.0 + np.exp(-steepness * (cosine_sim - midpoint)))

        # Stable softmax (shift-by-max) avoids overflow for large exponents.
        shifted_sim = cosine_sim - np.max(cosine_sim)
        exp_sim = np.exp(shifted_sim / self.temp)
        probs = exp_sim / np.sum(exp_sim)

        # Normalize so best hit has strength 1.0 and others are relative to it.
        strengths = probs / np.max(probs)

        return strengths, confidences

    def perceive(self, user_query: str):

        # Encode and normalize query using the same embedding setup as indexing time.
        query_vector = self.model.encode([user_query])
        query_vector = np.array(query_vector).astype("float32")

        faiss.normalize_L2(query_vector)

        distances, indecies = self.index.search(query_vector, self.top_k)

        distance_list = distances[0]
        index_list = indecies[0]

        strengths, confidence = self.calculate_stv(distance_list)

        sentences = []

        for i in range(self.top_k):
            # FAISS returns numeric ids; mapping file stores them as string keys in JSON.
            faiss_id = str(index_list[i])
            node_name = self.mapping.get(faiss_id, "UNKNOWN_NODE")

            s = strengths[i]
            c = confidence[i]

            # Convert retrieval output into MeTTa sentences with STV evidence metadata.
            stmt = f"(Sentence ((Inheritance {node_name} UserIntent) (stv {s:.3f} {c:.3f})) (UserEv{i + 1}))"
            sentences.append(stmt)

        return sentences


def main():

    index_path = "vector_DB/galaxy_index.faiss"
    mapping_path = "vector_DB/faiss_mapping.json"

    spark = PerceptionEngine(index_path=index_path, mapping_path=mapping_path)
    user_query = "I need a tool to align human RNA-seq reads to a reference genome, and it should handle splice junctions."

    metta_str = spark.perceive(user_query)

    print(metta_str[:10])


if __name__ == "__main__":
    main()
