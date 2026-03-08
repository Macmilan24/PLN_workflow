# run_pipeline.py
import argparse
from pathlib import Path

from main import main as build_offline_kb
from perception_engine import PerceptionEngine
from context_bubble import ContextBubbleBuilder
from downward_reasoner import DownwardReasoner
from workflow_assembly import WorkflowAssembler

REQUIRED_ARTIFACTS = [
    Path("metta_kbs/galaxy_topology.metta"),
    Path("metta_kbs/galaxy_history.metta"),
    Path("vector_DB/galaxy_index.faiss"),
    Path("vector_DB/faiss_mapping.json"),
]


def needs_bootstrap() -> bool:
    return any(not path.exists() for path in REQUIRED_ARTIFACTS)


def run_pipeline(
    user_query: str, rebuild: bool = False, max_steps: int = 50, max_length: int = 10
):
    should_build = rebuild or needs_bootstrap()
    if should_build:
        build_offline_kb()

    index_path = "vector_DB/galaxy_index.faiss"
    mapping_path = "vector_DB/faiss_mapping.json"
    bubble_path = "metta_kbs/context_bubble.metta"

    spark = PerceptionEngine(index_path=index_path, mapping_path=mapping_path)
    perception_results = spark.perceive(user_query)

    builder = ContextBubbleBuilder(
        history_path="metta_kbs/galaxy_history.metta",
        topology_path="metta_kbs/galaxy_topology.metta",
        rules_path="extraction_rules.metta",
    )
    context_bubble = builder.build_context(perception_results)

    Path("metta_kbs").mkdir(exist_ok=True)
    Path(bubble_path).write_text(context_bubble, encoding="utf-8")

    reasoner = DownwardReasoner(pln_file_path="pln.metta")
    master_list = reasoner.generate_master_list(
        bubble_file_path=bubble_path,
        max_steps=max_steps,
    )

    if not master_list:
        return {
            "query": user_query,
            "perception_results": perception_results,
            "context_bubble": context_bubble,
            "master_list": [],
            "workflow": [],
        }

    assembler = WorkflowAssembler(reasoner.metta)
    workflow = assembler.assemble_workflow(master_list, max_length=max_length)

    return {
        "query": user_query,
        "perception_results": perception_results,
        "context_bubble": context_bubble,
        "master_list": master_list,
        "workflow": workflow,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", help="Natural language workflow request")
    parser.add_argument(
        "--rebuild", action="store_true", help="Rebuild offline KB first"
    )
    parser.add_argument("--max-steps", type=int, default=50)
    parser.add_argument("--max-length", type=int, default=10)
    args = parser.parse_args()

    user_query = args.query or input("Enter your workflow request: ").strip()
    result = run_pipeline(
        user_query=user_query,
        rebuild=args.rebuild,
        max_steps=args.max_steps,
        max_length=args.max_length,
    )

    print("\n=== FINAL WORKFLOW ===")
    print(
        " -> ".join(result["workflow"])
        if result["workflow"]
        else "No workflow generated"
    )


if __name__ == "__main__":
    main()
