from neo4j import GraphDatabase
from typing import List, Dict, Any


class Neo4jConnector:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def execute_read_query(
        self, query: str, param: dict = None
    ) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(query, param or {})
            return [record.data() for record in result]
