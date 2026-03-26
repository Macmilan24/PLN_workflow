import sys
import os
import json
import re


from config import Config
from neo4j_client import Neo4jConnector


sys.path.append(os.path.abspath("PeTTa/python"))
from petta import PeTTa


class DownwardReasoner:
    def __init__(self, pln_file_path):
        self.metta = PeTTa()

        print("Fetching recognized Tools from Neo4j...")
        self.valid_tools_set = self._load_valid_tools_from_db()

        print(f"Loaded {len(self.valid_tools_set)} tools into memory.")

        print("Initializing MeTTa and loading PLN library...")
        self.metta.load_metta_file(pln_file_path)

    def _clean_symbol(self, val: str) -> str:
        if not val:
            return "Unknown"

        s = str(val).strip()
        if not s:
            return "Unknown"

        s = s.replace('"', "").replace("'", "")
        s = re.sub(r"\s+", "_", s)
        s = re.sub(r"[^A-Za-z0-9_]", "_", s)
        s = re.sub(r"_+", "_", s).strip("_")

        if not s:
            return "Unknown"
        if s[0].isdigit():
            s = f"S_{s}"
        return s

    def _load_valid_tools_from_db(self):
        # Initialize your specific connector using your config file
        db = Neo4jConnector(
            uri=Config.NEO4J_URI, user=Config.NEO4J_USER, password=Config.NEO4J_PASS
        )

        query = "MATCH (t:Tool) RETURN t.name AS raw_name"
        results = db.execute_read_query(query)

        tools_map = {}
        for record in results:
            raw_name = record.get("raw_name")
            if raw_name:
                cleaned_name = self._clean_symbol(raw_name)
                tools_map[cleaned_name] = raw_name

        db.close()

        return tools_map

    def generate_master_list(self, bubble_file_path, max_steps=50):
        print(f"Loading Context Bubble from {bubble_file_path}...")

        self.metta.process_metta_string("!(clear-atom-space! &bubble)")

        with open(bubble_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    self.metta.process_metta_string(f"!(add-atom &bubble {line})")
        print(f"Executing PLN Downward Reasoning for {max_steps} steps...")

        metta_output = self.metta.process_metta_string(
            f"!(Generate-Master-List {max_steps})"
        )

        result_str = str(metta_output)

        return self._extract_executable_tools(result_str)

    def _extract_executable_tools(self, metta_output_str):
        master_list = []
        seen_tools = set()

        pattern = re.compile(r"\(\s*([A-Za-z0-9_.-]+)\s+([0-9.]+)\s+([0-9.]+)\s*\)")

        for match in pattern.finditer(metta_output_str):
            node_name = match.group(1)
            strength = float(match.group(2))
            confidence = float(match.group(3))

            if node_name in self.valid_tools_set and node_name not in seen_tools:
                seen_tools.add(node_name)

                relevance_stv = strength * confidence

                master_list.append(
                    {
                        "tool": node_name,
                        "strength": strength,
                        "confidence": confidence,
                        "relevance_score": relevance_stv,
                    }
                )

        master_list.sort(key=lambda x: x["relevance_score"], reverse=True)
        return master_list


if __name__ == "__main__":

    # Initialize the Reasoner
    reasoner = DownwardReasoner(pln_file_path="pln.metta")

    # Run Phase 4 using the context bubble generated in Phase 3
    master_list = reasoner.generate_master_list(
        bubble_file_path="metta_kbs/context_bubble.metta", max_steps=50
    )

    print("\n--- PHASE 4: FINAL MASTER LIST ---")
    if not master_list:
        print(
            "No executable tools deduced. Try increasing max_steps or check Context Bubble."
        )
    else:
        for i, item in enumerate(master_list):
            print(
                f"{i+1}. {item['tool']} | Relevance: {item['relevance_score']:.3f} (S: {item['strength']:.2f}, C: {item['confidence']:.2f})"
            )
