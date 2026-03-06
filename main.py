import os
from config import Config
from neo4j_client import Neo4jConnector
from extractors import TopologyExtractor, HistoryExtractor
from vector_indexer import VectorIndexer


def write_kb(file_path: str, kb_name: str, sentences: list):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w") as f:
        f.write(f"( = ({kb_name}) ( \n")

        for sentence in sentences:
            f.write(f"{sentence}\n")

        f.write("))")

    print(f"Successfully wrote {len(sentences)} atoms to {file_path}")


def main():

    print("== Start extracting Knowledge base from Neo4J ==")

    db = Neo4jConnector(Config.NEO4J_URI, Config.NEO4J_USER, Config.NEO4J_PASS)

    try:
        print("Extracting the Toplogical KB ...")
        toplogy_extractor = TopologyExtractor(db, Config.TOPOLOGY_LIMIT)
        toplogy_sentence = toplogy_extractor.extract()
        write_kb(Config.TOPOLOGY_FILE, "Topology_kb", toplogy_sentence)

        print("Extracting the Historical KB ...")

        history_extractor = HistoryExtractor(
            db, Config.CONFIDENCE_K, Config.HISTORY_LIMIT
        )
        history_sentence = history_extractor.extract()
        write_kb(Config.HISTORY_FILE, "History_kb", history_sentence)

        print("Starting the Latent space embedding ...")

        indexer = VectorIndexer(db)
        indexer.extract_node()
        indexer.build_and_save_index()

    finally:
        db.close()
        print("\n Databases successfully compiled to .metta files.")


if __name__ == "__main__":
    main()
