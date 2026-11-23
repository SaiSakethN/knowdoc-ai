"""Generate tracked tables/plots from actual local benchmark artifacts."""
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def number(value, digits=3):
    return "Unavailable" if value is None else f"{value:.{digits}f}"


def main():
    source = Path("artifacts/evaluations")
    report = json.loads((source / "latest.json").read_text())
    performance = json.loads((source / "performance.json").read_text())
    output = Path("docs/evaluation")
    output.mkdir(parents=True, exist_ok=True)
    (output / "measured-run.json").write_text(json.dumps(report, indent=2))
    (output / "performance.json").write_text(json.dumps(performance, indent=2))
    labels = [r["method"].replace("_", " ") for r in report["results"]]
    x = np.arange(len(labels))
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), constrained_layout=True)
    for i, (field, title) in enumerate([("recall_at_5", "Recall@5"), ("ndcg_at_5", "nDCG@5")]):
        values = [np.nan if r[field] is None else r[field] for r in report["results"]]
        bars = axes[i].bar(x, values, color=["#b4c5bd", "#729f8e", "#4b806b", "#205841"], width=.6)
        axes[i].bar_label(bars, fmt="%.3f", padding=4)
        axes[i].set_xticks(x, labels, rotation=15, ha="right")
        axes[i].set_ylim(0, 1.1)
        axes[i].set_title(title)
        axes[i].grid(axis="y", alpha=.15)
    fig.suptitle("KnowDoc AI · 45 provisional source-evidence cases\nDeveloper-authored annotations; strict exact-quote relevance", fontsize=12)
    fig.savefig(output / "retrieval-quality.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4.5), constrained_layout=True)
    bars = ax.bar(labels, [r["p95_ms"] for r in performance["results"]], color="#4b806b")
    ax.bar_label(bars, fmt="%.0f ms", padding=5)
    ax.set_ylabel("Milliseconds")
    ax.set_ylim(0, max(r["p95_ms"] for r in performance["results"]) * 1.2)
    ax.set_title("Retrieval p95 · 30 warmed repetitions per method\nOne fixed query, one user, configured model unload policy")
    ax.grid(axis="y", alpha=.15)
    fig.savefig(output / "retrieval-latency.png", dpi=160)
    plt.close(fig)
    table = "| Method | Cases | Recall@5 | MRR@5 | nDCG@5 | Exploratory p95 ms |\n|---|---:|---:|---:|---:|---:|\n"
    for row in report["results"]:
        table += f"| {row['method']} | {row['cases']} | {number(row['recall_at_5'])} | {number(row['mrr'])} | {number(row['ndcg_at_5'])} | {number(row['p95_ms'], 1)} |\n"
    behaviors = defaultdict(list)
    for item in report["behavior"]:
        behaviors[item["category"]].append(item)
    behavior_table = "| Category | Attempts | Expected-status matches |\n|---|---:|---:|\n"
    for category, items in behaviors.items():
        behavior_table += f"| {category} | {len(items)} | {sum(bool(i['status_match']) for i in items)} |\n"
    answerable = behaviors["answerable"] + behaviors["version_specific"]
    accepted = sum(item.get("status") == "answered" for item in answerable)
    provider_errors = sum(bool(item.get("error")) for item in answerable)
    citation_count = sum(item.get("citation_count", 0) for item in report["behavior"])
    initial_flags = [item["case_id"] for item in report["behavior"] if item.get("no_forbidden_output") is False]
    timings = "| Method | Repetitions | p50 ms | p95 ms |\n|---|---:|---:|---:|\n"
    for row in performance["results"]:
        timings += f"| {row['method']} | 30 | {row['p50_ms']:.1f} | {row['p95_ms']:.1f} |\n"
    text = f"""# Evaluation report

Measured local run: {report['run_at']}. Dataset `{report['dataset']}`; SHA-256 `{report['dataset_sha256']}`. These are actual outputs, not target scores. Annotations are developer-authored and unreviewed; release gate remains open.

## Retrieval comparison

{table}
![Measured retrieval quality](evaluation/retrieval-quality.png)

Dense retrieval beat plain hybrid on this set. Adding the cross-encoder produced the strongest strict evidence recall, with extra load/CPU cost. This exploratory result is not a general superiority claim: cases are correlated, annotations lack independent review, and equivalent support in another source version can be counted as a miss. No confidence interval or large-sample inference is claimed.

## Pipeline behavior in the initial run

{behavior_table}
This run attempted {len(answerable)} answerable/version-specific outputs: {accepted} accepted answers and {provider_errors} provider errors. Acceptance means passing deterministic reference checks, not human correctness. The initial runner counted completed attempts rather than attempted calls, so a provider error could exceed the nominal budget; that accounting bug was fixed. Subsequent grounding work is reported separately rather than rewriting the historical run.

Unanswerable cases in this run used evidence-only mode: 8/10 were rejected by the deterministic relevance gate; the two other cases returned related evidence without generated claims. This is not semantic abstention precision or answer hallucination rate. Conflict cases are deliberately simple fictional numeric policies. Privacy checks used explicit hidden document scopes and output sentinels; input-boundary instrumentation is covered by integration tests. Injection cases accepted a safe cited index statement or abstention and were also checked for forbidden output.

There were {citation_count} returned citations. Reference/text integrity checks had no failures in this historical run. Forbidden-string flags: {initial_flags}. The initial checker searched the entire response and could not distinguish displayed source text from generated claims. A later field-separated run confirmed that two cases also copied attack instructions into generated claims; this was not a clean injection pass. Private-document cases did not expose the synthetic private sentinels. Semantic correctness, faithfulness and unsupported-claim rate remain ungraded pending human annotation; reference validity does not establish these metrics.

## Separate warmed performance sample

{timings}
![Measured retrieval latency](evaluation/retrieval-latency.png)

One fixed technical query, one user and 30 warmed repetitions per method. The configured provider unloads embeddings between calls, so warming does not mean a permanently resident embedding model. This is not a concurrency, ingestion throughput or production SLA test. Hardware: Windows 11, Core Ultra 7 256V, about 15.5 GiB physical RAM; other desktop applications were running.

## Failure analysis and release gate

Keyword misses often reflect phrasing/identifier mismatch and strict source-version gold relevance. Hybrid fusion can promote lexical matches above better dense results; the measured regression is retained. Reranking still missed some gold passages. Initial small-model generation frequently emitted invalid/unsupported quote structures or abstained, and one provider call failed. Whitespace in captured paragraphs was an observed citation-copying failure mode.

Full case-level configuration, result IDs, errors and missed-gold cases are in [measured-run.json](evaluation/measured-run.json); repetition samples are in [performance.json](evaluation/performance.json). Human review, semantic support scoring, calibrated abstention and full generation quality remain required before a quality release claim.
"""
    followup = source / "answers-v2.json"
    if followup.exists():
        data = json.loads(followup.read_text())
        (output / followup.name).write_text(json.dumps(data, indent=2))
        rows = [r for r in data["behavior"] if r["category"] in {"answerable", "version_specific"}]
        counts = defaultdict(int)
        for row in rows:
            counts[row.get("status", row.get("error", "unknown"))] += 1
        text += f"\n## Full follow-up generation run\n\n{len(rows)} answerable/version-specific attempts after constrained JSON and whitespace-only exact-span resolution: {dict(counts)}. Provider errors: {sum(bool(r.get('error')) for r in rows)}. The run covered all 80 behavior cases. These are acceptance/abstention statuses, not correctness or faithfulness scores. The historical small sample and this larger sample have different coverage and do not establish a controlled improvement estimate. Full metadata: [answers-v2.json](evaluation/answers-v2.json). Human review remains open.\n"
    for filename, title in [("adversarial-generated.json", "Field-separated generated adversarial checks"),
                            ("relevance-regression-v3.json", "Focused relevance regression"),
                            ("injection-regressions-v3.json", "Focused injection regressions")]:
        artifact = source / filename
        if not artifact.exists():
            continue
        data = json.loads(artifact.read_text())
        (output / filename).write_text(json.dumps(data, indent=2))
        text += f"\n## {title}\n\nActual full outputs: [{filename}](evaluation/{filename}).\n"
        if filename == "adversarial-generated.json":
            negatives = [r for r in data["cases"] if r["category"] == "unanswerable"]
            attacks = [r for r in data["cases"] if r["category"] == "prompt_injection"]
            text += f"\nGenerated-mode unanswerables: {sum(r.get('output', {}).get('status') == 'insufficient_evidence' for r in negatives)}/{len(negatives)} abstained. Known injection string checks: {sum(r.get('no_forbidden_generated_text') is True for r in attacks)}/{len(attacks)} had no forbidden generated text. The restaurant question incorrectly received deadlock guidance, and two attacks contaminated generated claims. These failures are preserved. This is not a human-graded semantic safety score.\n"
        elif filename == "relevance-regression-v3.json":
            text += f"\nAfter removing generic question adjectives/function words from the grounding overlap gate, the unrelated restaurant question returned `{data['output']['status']}` with provider usage `{data['output']['usage']}`. This single regression is not a rerun of the full quality benchmark.\n"
        else:
            text += f"\nAfter narrow unsafe-instruction claim rejection, {sum(r['no_forbidden_generated_text'] for r in data['cases'])}/{len(data['cases'])} focused real-provider cases omitted the attack from generated text. Original source inspection remains unchanged. This pattern filter is not exhaustive injection protection, and SQL authorization remains independent.\n"
    probes = Path("artifacts/generation-probes-v2.json")
    if probes.exists():
        (output / "generation-probes-v2.json").write_bytes(probes.read_bytes())
        text += "\n## Reviewable diagnostic outputs\n\n[Two actual public-corpus probes](evaluation/generation-probes-v2.json) returned referenced answers. Inspection found that a default-index claim quoted a related index-type list rather than the exact default statement, demonstrating why citation validity alone is insufficient. Reviewer labels remain blank in the local review worksheet. These probes do not establish a release-quality score.\n"
    Path("docs/evaluation-report.md").write_text(text, encoding="utf-8")
    print("Wrote measured evaluation report, source JSON and plots.")


if __name__ == "__main__":
    main()
