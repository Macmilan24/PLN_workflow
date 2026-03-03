import json

with open("history.json", "r") as f:
    data = json.load(f)

k_saturation = 10
metta_sentences = []
evidence_counter = 1

output_lines = []
output_lines.append("; --- AUTO-GENERATED PLN KNOWLEDGE BASE ---")
output_lines.append("(= (KB) (")

for parent, children in data.items():
    N = sum(children.values())

    for child, n in children.items():
        s = n / N

        c = N / (N + k_saturation)

        sentence = f"  (Sentence ((Implication {parent} {child}) (stv {s:.3f} {c:.3f})) (Ev{evidence_counter}))"
        metta_sentences.append(sentence)
        evidence_counter += 1

output_lines.append("\n".join(metta_sentences))
output_lines.append("))")

output_lines.append(
    "\n; Default node probabilities required by PLN's Truth_Deduction formula"
)
output_lines.append("(= (STV $x) (stv 0.5 0.5))")

with open("kb.metta", "w") as f:
    f.write("\n".join(output_lines) + "\n")

print("Wrote kb.metta")
