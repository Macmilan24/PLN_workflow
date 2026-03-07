import os


class Config:
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://37.27.231.93:7990")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASS = os.getenv("NEO4J_PASS", "abc12345")

    CONFIDENCE_K = 5.0

    TOPOLOGY_LIMIT = int(os.getenv("TOPOLOGY_LIMIT", "100000"))
    HISTORY_LIMIT = int(os.getenv("HISTORY_LIMIT", "100000"))

    OUTPUT_DIR = "metta_kbs"
    VECTOR_OUTPUT_DIR = "vector_DB"
    TOPOLOGY_FILE = os.path.join(OUTPUT_DIR, "galaxy_topology.metta")
    HISTORY_FILE = os.path.join(OUTPUT_DIR, "galaxy_history.metta")
