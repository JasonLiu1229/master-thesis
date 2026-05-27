# Made with Claude sonnet 4.6

import json
import matplotlib.pyplot as plt
import numpy as np
import os

DATA = json.load(open("out/cloud/gpt-4.1/t3_benchmark_results_per_file.json"))
# Sort by filename for consistent ordering
DATA = sorted(DATA, key=lambda x: x["filename"])

OUT = "out/cloud/gpt-4.1/"
os.makedirs(OUT, exist_ok=True)

# Short labels: strip "TestClass" and ".java.jsonl"
labels = [
    d["filename"].replace("TestClass", "").replace(".java.jsonl", "") for d in DATA
]

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
    }
)

BLUE = "#2563EB"
RED = "#DC2626"
GREEN = "#16A34A"
ORANGE = "#EA580C"
GREY = "#6B7280"


def make_per_file_plot(
    values,
    title,
    xlabel,
    filename,
    color=BLUE,
    xlim=None,
    mean_color=RED,
    extra_lines=None,
):
    """
    values      : list of floats, one per file
    extra_lines : list of (value, color, label) for extra vertical lines
    """
    n = len(values)
    fig_h = max(12, n * 0.22)
    fig, ax = plt.subplots(figsize=(10, fig_h))

    y = np.arange(n)
    ax.barh(y, values, 0.7, color=color, alpha=0.85)

    mean_val = np.mean(values)
    ax.axvline(
        mean_val,
        color=mean_color,
        linestyle="--",
        linewidth=1.5,
        label=f"Mean = {mean_val:.3f}",
    )

    if extra_lines:
        for val, col, lbl in extra_lines:
            ax.axvline(val, color=col, linestyle=":", linewidth=1.3, label=lbl)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_title(title, fontweight="bold", pad=10, fontsize=11)
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)
    if xlim:
        ax.set_xlim(*xlim)
    ax.legend(fontsize=8, loc="lower right")

    plt.tight_layout()
    path = os.path.join(OUT, filename)
    plt.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"Saved {filename}")


# ── 1. F1 ─────────────────────────────────────────────────────────────────────
make_per_file_plot(
    values=[d["f1"] for d in DATA],
    title="F1 Score per Test File",
    xlabel="F1",
    filename="pf_f1.png",
    color=BLUE,
    xlim=(0, 1.05),
    extra_lines=[
        (0.019, ORANGE, "GGNN baseline (0.019)"),
        (0.308, GREEN, "RefBERT baseline (0.308)"),
    ],
)

# ── 2. Precision ──────────────────────────────────────────────────────────────
make_per_file_plot(
    values=[d["precision"] for d in DATA],
    title="Precision per Test File",
    xlabel="Precision",
    filename="pf_precision.png",
    color=BLUE,
    xlim=(0, 1.05),
)

# ── 3. Recall ─────────────────────────────────────────────────────────────────
make_per_file_plot(
    values=[d["recall"] for d in DATA],
    title="Recall per Test File",
    xlabel="Recall",
    filename="pf_recall.png",
    color=GREEN,
    xlim=(0, 1.05),
)

# ── 4. CER ────────────────────────────────────────────────────────────────────
make_per_file_plot(
    values=[d["cer"] for d in DATA],
    title="Character Error Rate (CER) per Test File\n(lower is better)",
    xlabel="CER (%)",
    filename="pf_cer.png",
    color=RED,
    xlim=(0, 105),
)

# ── 5. LLM Readability Score — renamed vs oracle ──────────────────────────────
renamed = [d["llm_renamed_avg"] for d in DATA]
oracle = [d["llm_oracle_avg"] for d in DATA]
obf = [d["llm_obf_avg"] for d in DATA]

n = len(DATA)
y = np.arange(n)
fig_h = max(12, n * 0.28)
fig, ax = plt.subplots(figsize=(10, fig_h))

h = 0.25
ax.barh(y - h, obf, h, color=GREY, alpha=0.85, label="Obfuscated")
ax.barh(y, renamed, h, color=BLUE, alpha=0.85, label="Renamed")
ax.barh(y + h, oracle, h, color=GREEN, alpha=0.85, label="Oracle (human)")

mean_renamed = np.mean(renamed)
mean_oracle = np.mean(oracle)
ax.axvline(
    mean_renamed,
    color=BLUE,
    linestyle="--",
    linewidth=1.5,
    label=f"Mean renamed = {mean_renamed:.1f}",
)
ax.axvline(
    mean_oracle,
    color=GREEN,
    linestyle="--",
    linewidth=1.5,
    label=f"Mean oracle = {mean_oracle:.1f}",
)

ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=6.5)
ax.set_xlabel("LLM Readability Score (0–100)", fontsize=10)
ax.set_title(
    "LLM Readability Score per Test File\n(obfuscated vs renamed vs oracle)",
    fontweight="bold",
    pad=10,
    fontsize=11,
)
ax.set_xlim(0, 105)
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.3)
ax.legend(fontsize=8, loc="lower right")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "pf_llm_score.png"), bbox_inches="tight")
plt.close()
print("Saved pf_llm_score.png")

# ── 6. Exact Match (ordered) ──────────────────────────────────────────────────
make_per_file_plot(
    values=[d["correct_ordered"] for d in DATA],
    title="Exact Match (Ordered) per Test File",
    xlabel="Exact Match",
    filename="pf_exact_ordered.png",
    color=ORANGE,
    xlim=(0, 1.05),
)

print(f"\nAll per-file figures saved to {OUT}")
