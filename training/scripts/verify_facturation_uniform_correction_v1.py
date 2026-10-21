"""Verify uniform-SFT terminal evidence without loading model weights."""
import hashlib
import math
from pathlib import Path

import facturation_uniform_correction_training_v1 as recipe
import verify_facturation_semantic_correction_v2 as records

LEGACY_VERIFIER_SHA256 = "993cec48fe7158d87b5496ade17d4dc41addd40c156487fbc320514a48a52c28"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def uniform_validation(loss):
    require(set(loss) == {"micro", "macro", "by_application", "unweighted"}
            and set(loss["unweighted"]) == {"micro", "macro", "by_application"},
            "Unexpected validation summary fields")
    plain = loss["unweighted"]
    require(set(loss["by_application"]) == set(plain["by_application"]),
            "Weighted/unweighted application inventory differs")
    pairs = [(loss[key], plain[key]) for key in ("micro", "macro")]
    pairs += [(value, plain["by_application"][app])
              for app, value in loss["by_application"].items()]
    for weighted, unweighted in pairs:
        require(all(type(value) in (int, float) and math.isfinite(value) and value >= 0
                    for value in (weighted, unweighted))
                and math.isclose(weighted, unweighted, rel_tol=1e-7, abs_tol=1e-9),
                "Uniform weighted/unweighted validation losses differ")


def verify(report, provenance, history, saved_selection, log, selection_source,
           selection_sha256, *, pins, parent_artifacts, dependency_versions,
           model_path, data_path, output_path):
    """Couple raw terminal records, trusted paths and equal-token loss summaries."""
    require(hashlib.sha256(Path(records.__file__).read_bytes()).hexdigest()
            == LEGACY_VERIFIER_SHA256, "Pinned terminal verifier changed")
    recipe.validate_training_report(report, pins, parent_artifacts, dependency_versions, True)
    config = report["training_config"]
    require(report["model_path"] == str(model_path)
            and config["model_path"] == str(model_path)
            and config["data_path"] == str(data_path)
            and config["output_path"] == str(output_path),
            "Reported training paths differ from the trusted binding")
    result = records.verify(report, provenance, history, saved_selection, log,
                            selection_source, selection_sha256)
    for entry in history:
        uniform_validation(entry["loss"])
    return {**result, "binding_paths_verified": True,
            "uniform_weighted_unweighted_consistent": True,
            "production_activation": False}
