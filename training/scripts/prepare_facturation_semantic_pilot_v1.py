"""Assemble a 500-row TRAIN-only pilot from two reviewed immutable preparations.

No model is loaded. All 384 replay rows and 116 clarified contrasts are copied
byte-for-byte; frozen validation and scoring remain unchanged.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

SEMANTIC = {
    "manifest.json": "ba8613f903ba1097f5d86a7a40ecf65ebc18b4c5c708a52dba8a7b3591b41dfa",
    "train.jsonl": "439c1147c0131c79d7c00749a4a024a813ad1f9e96e5baae81bc9ed2a2d423d0",
    "contrasts.jsonl": "0a633ab1d423c42d724533a95672cf9917636f3d4ea23396a3635e695c20b1fa",
    "valid.jsonl": "8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487",
}
REPLAY = {
    "manifest.json": "b147a7dd62b318b114ca516158351dcdb396be50a77f56300ca8917b74da8e8f",
    "train.jsonl": "9baf470b8d550201028b49d1caff029fe3aca8fdfc5df12799a6617bc4285360",
    "retained-plan.json": "bb0caa2191f54c27171d2b2202f03d6e8ef650829250de3c95154346835f7e03",
}
TRAIN_SHA256 = "05e792a632ba37cdbb71845e57c0444f4feb4c94851addc5ec84a9674da0cb0d"
EXPOSURE = {"facturation": 316, "management_projet": 112, "design_workflow": 72}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pinned(directory, expected):
    raw = {name: (directory / name).read_bytes() for name in expected}
    if any(sha(raw[name]) != digest for name, digest in expected.items()):
        raise ValueError("Reviewed preparation bytes changed")
    return raw


def assemble(replay, semantic):
    replay_lines = replay["train.jsonl"].splitlines()
    semantic_lines = semantic["train.jsonl"].splitlines()
    contrasts = semantic["contrasts.jsonl"].splitlines()
    if (len(replay_lines), len(semantic_lines), len(contrasts)) != (384, 820, 116):
        raise ValueError("Complete reviewed inventories required")
    if len(set(replay_lines)) != 384 or not set(replay_lines) <= set(semantic_lines[:704]):
        raise ValueError("Replay must be a byte-identical subset of the original inventory")
    if semantic_lines[704:] != contrasts:
        raise ValueError("All clarified contrasts must match the reviewed TRAIN suffix")
    combined = b"\n".join(replay_lines + contrasts) + b"\n"
    if sha(combined) != TRAIN_SHA256:
        raise ValueError("Exact 500-row pilot identity changed")
    rows = [json.loads(line) for line in combined.splitlines()]
    if Counter(row["application"] for row in rows) != Counter(EXPOSURE):
        raise ValueError("Application exposure changed")
    return combined


def prepare(replay, semantic, output):
    replay, semantic, output = [Path(p).resolve() for p in (replay, semantic, output)]
    if (output.exists() or not output.parent.is_dir()
            or any(output == p or p in output.parents for p in (replay, semantic))):
        raise ValueError("A new isolated output with an existing parent is required")
    old, new = pinned(replay, REPLAY), pinned(semantic, SEMANTIC)
    train = assemble(old, new)
    files = {"train.jsonl": train, "valid.jsonl": new["valid.jsonl"],
             "retained-plan.json": old["retained-plan.json"],
             "contrasts.jsonl": new["contrasts.jsonl"]}
    plan = json.loads(old["retained-plan.json"])["applications"]["facturation"]
    coverage = {
        "native_tools": len(plan["by_tool"]),
        "measured_features": {
            key: sum(value[key] for value in plan["feature_coverage"].values())
            for key in ("selected", "available")},
        "critical_conjunctions": plan["priority_conjunction_coverage"],
        "offered_tool_bundles": plan["offered_tool_bundle_coverage"],
    }
    if (coverage["native_tools"] != 18
            or coverage["measured_features"] != {"selected": 174, "available": 174}
            or any(coverage[key] != {"selected": n, "available": n, "uncovered": []}
                   for key, n in (("critical_conjunctions", 51), ("offered_tool_bundles", 58)))):
        raise ValueError("Recorded structural coverage changed")
    manifest = {
        "version": "facturation-semantic-pilot-v1-en-fr",
        "status": "PREPARED ONLY; NOT TRAINED OR ACCEPTED",
        "count": 500, "by_application": EXPOSURE,
        "applications": list(EXPOSURE), "languages": ["en", "fr"],
        "source_sha256": {"replay": REPLAY, "semantic": SEMANTIC},
        "files": {name: sha(raw) for name, raw in files.items()},
        "generator_sha256": sha(Path(__file__).read_bytes()),
        "coverage": coverage,
        "validation_unchanged": True,
        "limitations": [
            "Structural coverage is not functional accuracy or proven retention.",
            "Only 128 of 448 native Facturation replay rows are retained.",
            "All 72 entity contrasts, 116 semantic contrasts, 112 Management Projet "
            "and 72 Design Workflow replay rows are retained.",
            "Requires server preflight, numerical review and unchanged functional evaluation.",
        ],
        "training_executed": False, "model_accepted": False, "production_activation": False,
    }
    output.mkdir(mode=0o700)
    for name, raw in files.items():
        (output / name).write_bytes(raw)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("replay", "semantic", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.replay, args.semantic, args.output), indent=2))
