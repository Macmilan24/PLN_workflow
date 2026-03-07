import sys
import os
import re


from downward_reasoner import DownwardReasoner


class WorkflowAssembler:
    def __init__(self, metta):
        self.metta = metta

    def assemble_workflow(self, master_list, max_length=10):
        self.metta.process_metta_string("!(clear-atom-space! &masterlist)")
        for i, item in enumerate(master_list):
            tool = item["tool"]
            s = item["strength"]
            c = item["confidence"]

            self.metta.process_metta_string(
                f"!(add-atom &masterlist (Sentence ((Relevance {tool}) (stv {s:.3f} {c:.3f})) (UserEv{i})))"
            )

        current_tool = master_list[0]["tool"]
        workflow_chain = [current_tool]
        print(
            f"\n[START] Selected Anchor Node: {current_tool} (Relevance: {master_list[0]['relevance_score']:.3f})"
        )

        for step in range(max_length):
            metta_output = self.metta.process_metta_string(
                f"!(Predict-Next {current_tool})"
            )
            candidates = self._parse_predictions(str(metta_output))
            if not candidates:
                print(
                    f"[END] No further historical implications found. Workflow reached natural terminus."
                )
                break

            candidates = [c for c in candidates if c["tool"] not in workflow_chain]

            if not candidates:
                print(
                    f"[END] All predicted tools are already in the pipeline (Cycle prevented)."
                )
                break

            winner = candidates[0]

            print(f"winner: {winner['tool']} | score: {winner['score']:.3f}")
            workflow_chain.append(winner["tool"])

            current_tool = winner["tool"]

        return workflow_chain

    def _parse_predictions(self, metta_output_str):
        candidates = []

        pattern = re.compile(r"\(\s*([A-Za-z0-9_.-]+)\s+([0-9.]+)\s+([0-9.]+)\s*\)")

        for match in pattern.finditer(metta_output_str):
            tool = match.group(1)
            strength = float(match.group(2))
            confidence = float(match.group(3))

            candidates.append(
                {"tool": tool, "score": strength * confidence}  # Synergy Score
            )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates


if __name__ == "__main__":
    print("==================================================")
    print("   AI GALAXY WORKFLOW GENERATOR - SYSTEM START")
    print("==================================================")

    reasoner = DownwardReasoner(pln_file_path="pln.metta")
    master_list = reasoner.generate_master_list(
        bubble_file_path="metta_kbs/context_bubble.metta", max_steps=50
    )

    if not master_list:
        print(" Failed to generate Master List. The Context Bubble might be empty.")
        exit()

    print("\nInitiating Workflow Assembly...")

    assembler = WorkflowAssembler(reasoner.metta)

    final_pipeline = assembler.assemble_workflow(master_list, max_length=10)

    print("\n==================================================")
    print(" FINAL EXECUTABLE GALAXY WORKFLOW GENERATED:")
    print("==================================================")

    # Print the beautiful pipeline chain
    print("\n   " + " -> ".join(final_pipeline) + "\n")

    print("==================================================")
