# MeTTa Practice: Galaxy Workflow Assembly

This project builds Galaxy workflow recommendations from a natural-language query by combining five stages:

1. Offline knowledge extraction from Neo4j into MeTTa knowledge bases.
2. Semantic retrieval over a FAISS vector index.
3. Context-bubble extraction in MeTTa.
4. Downward reasoning to produce a ranked master list of executable tools.
5. Forward workflow assembly using historical implication links.

The main entry point is `run_pipeline.py`.

## Project Layout

- `main.py`: offline build step for topology, history, and vector index artifacts.
- `run_pipeline.py`: end-to-end orchestrator.
- `perception_engine.py`: semantic retrieval from the vector index.
- `context_bubble.py`: extracts the local reasoning subgraph.
- `downward_reasoner.py`: derives the ranked tool master list.
- `workflow_assembly.py`: assembles the final workflow chain.
- `metta_kbs/`: generated `.metta` knowledge bases.
- `vector_DB/`: generated FAISS index and mapping.
- `PeTTa/`: local clone of the PeTTa runtime used by the MeTTa integration.

## Requirements

- Python 3.12 or compatible Python 3.x environment.
- SWI-Prolog installed and available on the system.
- Access to the Neo4j database configured in `config.py` or via environment variables.
- A local clone of PeTTa in the project root as `./PeTTa`.

This code imports PeTTa directly from `PeTTa/python`, so cloning PeTTa is required.

## Clone PeTTa

If `PeTTa/` is not already present in the repository root, clone it before running the project:

```bash
git clone https://github.com/patham9/PeTTa.git PeTTa
```

PeTTa upstream notes that it depends on SWI-Prolog and Python interop support.

## Python Setup

If you already have the included virtual environment and it works on your machine, activate it. Otherwise create a new one.

### Using the existing virtual environment

On WSL/Linux:

```bash
source metta_env/bin/activate
```

### Creating a new virtual environment

```bash
python3 -m venv metta_env
source metta_env/bin/activate
pip install -r requirements.txt
```

## Neo4j Configuration

The project reads these variables from the environment, with defaults defined in `config.py`:

- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASS`
- `TOPOLOGY_LIMIT`
- `HISTORY_LIMIT`

Example:

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASS=your_password
```

## How First Run Works

`run_pipeline.py` checks whether these required offline artifacts exist:

- `metta_kbs/galaxy_topology.metta`
- `metta_kbs/galaxy_history.metta`
- `vector_DB/galaxy_index.faiss`
- `vector_DB/faiss_mapping.json`

If any of them are missing, it automatically runs the offline build first.

That offline build does three things:

1. Extracts topology relations from Neo4j into `metta_kbs/galaxy_topology.metta`.
2. Extracts historical tool transitions into `metta_kbs/galaxy_history.metta`.
3. Builds the FAISS semantic index into `vector_DB/`.

So on a fresh machine, you can start with the pipeline directly and it will bootstrap the offline artifacts before semantic retrieval begins.

## Run The Full Pipeline

From the project root:

```bash
python run_pipeline.py "I need a fast and accurate RNA-seq workflow for human reads"
```

If artifacts are missing, this first run will build them automatically.

### Force a rebuild

Use this when you want to regenerate the offline knowledge bases and vector index:

```bash
python run_pipeline.py --rebuild "I need a fast and accurate RNA-seq workflow for human reads"
```

### Tune reasoning depth

```bash
python run_pipeline.py --max-steps 80 --max-length 12 "I need a splice-aware RNA-seq alignment and quantification workflow"
```

### Interactive mode

If no query is passed, the script prompts for one:

```bash
python run_pipeline.py
```

## Run Only The Offline Build

If you want to precompute everything without running the full query pipeline:

```bash
python main.py
```

This generates:

- `metta_kbs/galaxy_topology.metta`
- `metta_kbs/galaxy_history.metta`
- `vector_DB/galaxy_index.faiss`
- `vector_DB/faiss_mapping.json`

## Execution Flow

When you run `run_pipeline.py`, the pipeline executes in this order:

1. Check for required offline artifacts.
2. Build missing artifacts if necessary.
3. Convert the user query into semantic evidence with `PerceptionEngine`.
4. Build a context bubble around the retrieved nodes.
5. Run downward PLN reasoning to generate the master list.
6. Assemble the final workflow chain using historical implications.

## Typical Output

The final line printed by the orchestrator is the generated tool chain, for example:

```text
=== FINAL WORKFLOW ===
HISAT2 -> StringTie -> GffCompare
```

The exact output depends on your Neo4j data, generated offline artifacts, and the natural-language query.

## Troubleshooting

### `ModuleNotFoundError: petta`

Make sure the PeTTa repository is cloned into `./PeTTa` exactly.

### `faiss.read_index` fails

This usually means the vector index has not been built yet or the build failed. Run:

```bash
python main.py
```

or force a full rebuild:

```bash
python run_pipeline.py --rebuild "your query"
```

### Neo4j connection errors

Check `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASS`, and confirm the database is reachable.

### PeTTa runtime issues

Make sure SWI-Prolog is installed and available in the environment where you run the project.

## Notes

- `pln.metta` imports PLN support and may fetch required repositories on first use.
- `metta_kbs/context_bubble.metta` is generated during pipeline execution as an intermediate artifact.
- The quality of the final workflow depends heavily on the quality of the Neo4j topology, historical workflow data, and textual metadata used for embeddings.