from neo4j import GraphDatabase
from typing import List, Dict, Any


class Neo4jConnector:
    def __init__(self, uri, user, password):
        # Keep one driver per connector; sessions are opened per query.
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def execute_read_query(
        self, query: str, param: dict = None
    ) -> List[Dict[str, Any]]:
        # Session context manager ensures clean resource handling per transaction.
        with self._driver.session() as session:
            result = session.run(query, param or {})
            # Convert Neo4j Record objects into plain dicts for easier downstream use.
            return [record.data() for record in result]
