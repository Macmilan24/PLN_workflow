from neo4j_client import Neo4jConnector
from typing import List
import re


class KnowledgeExtractor:
    def __init__(self, db: Neo4jConnector):
        self.db = db

    def _clean_symbol(self, val: str) -> str:
        if not val:
            return "Unknown"

        s = str(val).strip()
        if not s:
            return "Unknown"

        # Normalize raw names into deterministic symbols safe for MeTTa atoms.
        s = s.replace('"', "").replace("'", "")
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^A-Za-z0-9_]", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")

        if not s:
            return "Unknown"
        if s[0].isdigit():
            s = f"S_{s}"
        return s

    def extract(self) -> List[str]:
        raise NotImplementedError("extract must be implemented by subclass")


class TopologyExtractor(KnowledgeExtractor):
    def __init__(self, db: Neo4jConnector, limit: int = 1000):
        super().__init__(db)
        self.limit = limit

    def extract(self) -> List[str]:
        sentences = []

        # Pull structural edges only, then canonicalize node names before atom generation.
        query = """
                MATCH (parent)-[r]->(child)
                WHERE type(r) in ['HAS_WORKFLOW', 'HAS_STEP', 'STEP_USES_TOOL']
                WITH
                    coalesce(parent.name, parent.file_name, parent.id, 'Unknown') AS parent_name,
                    coalesce(child.name, child.file_name, child.id,  'Unknown') AS child_name
                RETURN DISTINCT parent_name, child_name
                ORDER BY parent_name, child_name
                LIMIT $limit
                """
        result = self.db.execute_read_query(query, {"limit": self.limit})
        ev_count = 1

        for row in result:
            parent = self._clean_symbol(row["parent_name"])
            child = self._clean_symbol(row["child_name"])

            # Topology atoms are treated as factual structure, so stv is fixed to 1.0.
            stmt = f"   (Sentence ((Inheritance {parent} {child}) (stv 1.00 1.00)) (TEv{ev_count}))"
            sentences.append(stmt)
            ev_count += 1

        return sentences


class HistoryExtractor(KnowledgeExtractor):
    def __init__(self, db: Neo4jConnector, k: float, limit: int = 100):
        super().__init__(db)
        self.k = k
        self.limit = limit

    def extract(self) -> List[str]:
        sentences = []

        # Two-step query:
        # 1) count transitions tool_a -> tool_b
        # 2) count all outgoing transitions from tool_a to compute conditional strength
        query = """
                MATCH (t1:Tool)<-[:STEP_USES_TOOL]-(s1:Step)-[:NEXT_STEP|STEP_FEEDS_INTO]->(s2:Step)-[:STEP_USES_TOOL]->(t2:Tool)
                WITH t1.name AS tool_a, t2.name AS tool_b, count(*) AS transition_count
        
                MATCH (:Tool {name: tool_a})<-[:STEP_USES_TOOL]-(:Step)-[:NEXT_STEP|STEP_FEEDS_INTO]->(:Step)-[:STEP_USES_TOOL]->(:Tool)
                WITH tool_a, tool_b, transition_count, count(*) AS total_outgoing
        
                RETURN tool_a, tool_b, transition_count, total_outgoing
                LIMIT $limit
                """

        result = self.db.execute_read_query(query, {"limit": self.limit})
        ev_count = 1

        for row in result:
            tool_a = self._clean_symbol(row["tool_a"])
            tool_b = self._clean_symbol(row["tool_b"])

            n_ab = row["transition_count"]
            n_a = row["total_outgoing"]

            # strength approximates P(tool_b | tool_a), confidence uses k-smoothing.
            strength = n_ab / n_a if n_a > 0 else 0.0
            confidence = n_ab / (n_ab + self.k)
            stmt = f"   (Sentence ((Implication {tool_a} {tool_b}) (stv {strength:.3f} {confidence:.3f})) (HEv{ev_count}))"
            sentences.append(stmt)
            ev_count += 1

        return sentences
