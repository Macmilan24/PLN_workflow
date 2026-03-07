import sys
import os
from perception_engine import PerceptionEngine

sys.path.append(os.path.abspath("PeTTa/python"))
from petta import PeTTa


class ContextBubbleBuilder:
    def __init__(self, history_path, topology_path, rules_path):
        self.metta = PeTTa()

        self.metta.process_metta_string("!(bind! &global (new-space))")
        self.metta.process_metta_string("!(bind! &bubble (new-space))")

        print("Loading Knowledge Base... (This happens once on server start)")

        self._load_file_to_space(history_path, "&global")
        self._load_file_to_space(topology_path, "&global")

        # 3. Load the Extraction Logic into the main runner
        with open(rules_path, "r") as f:
            self.metta.process_metta_string(f.read())

        print("Knowledge Base Loaded. System Ready.")

    def _load_file_to_space(self, file_path, space_name):

        try:
            with open(file_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line:
                        self.metta.process_metta_string(
                            f"!(add-atom {space_name} {line})"
                        )
            print(f"Successfully loaded {file_path} into {space_name}")

        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    def build_context(self, perception_results):

        print(f"Building Context Bubble for {len(perception_results)} seeds...")

        self.metta.process_metta_string("!(clear-atom-space! &bubble)")

        for atom_str in perception_results:
            self.metta.process_metta_string(f"!(add-atom &bubble {atom_str})")

        # Extract Seeds from the Bubble
        result = self.metta.process_metta_string(
            "!(match &bubble (Sentence ((Inheritance $seed UserIntent) $stv) $ev) $seed)"
        )

        seeds = [str(r) for r in result]

        # For every seed, we call the MeTTa function defined in extraction_rules.metta
        for seed in seeds:
            self.metta.process_metta_string(
                f"!(extract-context-for-node {seed} &global &bubble)"
            )

        # Export the Bubble
        bubble_content = self.metta.process_metta_string("!(match &bubble $atom $atom)")

        # Convert atoms back to string representation
        bubble_str_list = [str(atom) for atom in bubble_content]

        return "\n".join(bubble_str_list)


if __name__ == "__main__":

    index_path = "vector_DB/galaxy_index.faiss"
    mapping_path = "vector_DB/faiss_mapping.json"

    spark = PerceptionEngine(index_path=index_path, mapping_path=mapping_path)

    builder = ContextBubbleBuilder(
        history_path="metta_kbs/galaxy_history.metta",
        topology_path="metta_kbs/galaxy_topology.metta",
        rules_path="extraction_rules.metta",
    )

    user_query = "I need a tool to align human RNA-seq reads to a reference genome, and it should handle splice junctions."

    metta_str = spark.perceive(user_query)

    # Run extraction
    context_bubble = builder.build_context(metta_str)

    print("\n--- GENERATED CONTEXT BUBBLE ---")
    print(context_bubble[:500] + "...")

    # Save to file for Phase 4
    with open("metta_kbs/context_bubble.metta", "w") as f:
        f.write(context_bubble)
