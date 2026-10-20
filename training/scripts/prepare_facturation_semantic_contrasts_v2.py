"""Clarify TRAIN recency and calendar intent without changing frozen evaluations.

Reproduce the reviewed v1 preparation first. Keep its entire 704-row replay,
validation bytes, permission schemas and trusted history unchanged.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory

VERSION = "facturation-semantic-contrasts-v2-en-fr"
PRIOR_SHA256 = "3d7f2eee56c328593d8ccfbd01c4aea1e637da0b6a4d13079ee48d5489d27d43"
REFERENCE_MANIFEST_SHA256 = "cccefb636438ffeeb2fad4fd32bae4a3d93d27d07582a087b4303efe5539e320"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prior():
    path = Path(__file__).with_name("prepare_facturation_semantic_contrasts_v1.py")
    if sha(path.read_bytes()) != PRIOR_SHA256:
        raise ValueError("Reviewed v1 generator identity changed")
    spec = importlib.util.spec_from_file_location("reviewed_semantic_contrasts_v1", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def clarify_rows(original):
    v1 = prior()
    result = deepcopy(original)
    changed_recency = changed_month = month_to_date = 0
    for row, source in zip(result, original):
        metadata = row["augmentation"]
        family, factors = metadata["family"], metadata["factors"]
        prefix, text = v1.helper().current_request(row["messages"][-2]["content"])
        before = v1.target(source)
        if family == "date_boundaries" and factors["mode"] != "unbounded":
            old = ("Retrieve the valid payments " if row["language"] == "en" else
                   "Récupère les règlements valides ")
            new = ("Retrieve the most recent valid payments " if row["language"] == "en" else
                   "Récupère les règlements valides les plus récents ")
            if not text.startswith(old):
                raise ValueError("Expected bounded payment TRAIN wording changed")
            text = new + text[len(old):]
            changed_recency += 1
        elif family == "relative_quote_month":
            context = v1.trusted_context(row)
            previous, index = factors["previous"], factors["paraphrase"]
            if previous:
                phrases = {
                    "en": ["Find up to 3 quotes dated within the entire previous calendar month.",
                           "Retrieve at most 3 quotes from the first through the last day of last month.",
                           "List no more than 3 quotes covering last month’s complete calendar date range."],
                    "fr": ["Retrouve au plus 3 devis datés pendant le mois calendaire précédent en entier.",
                           "Recherche au maximum 3 devis du premier au dernier jour du mois dernier.",
                           "Liste jusqu’à 3 devis sur toute la période calendaire du mois dernier."],
                }
                end_mode = "calendar_last_day"
            else:
                phrases = {
                    "en": ["Find up to 3 quotes dated anywhere in this entire calendar month, through its last day.",
                           "Retrieve at most 3 quotes from the start of this month through today, inclusive.",
                           "List no more than 3 quotes over this month’s full calendar date range, including dates after today."],
                    "fr": ["Retrouve au plus 3 devis sur ce mois calendaire en entier, jusqu’à son dernier jour.",
                           "Recherche au maximum 3 devis depuis le début de ce mois jusqu’à aujourd’hui inclus.",
                           "Liste jusqu’à 3 devis sur toute la période calendaire de ce mois, y compris les dates après aujourd’hui."],
                }
                end_mode = "today" if index == 1 else "calendar_last_day"
            text = phrases[row["language"]][index]
            arguments = row["messages"][-1]["tool_calls"][0]["function"]["arguments"]
            start, end = v1.month_bounds(context["today"], previous)
            if end_mode == "today":
                end = context["today"]
                month_to_date += 1
            arguments["date_from"], arguments["date_to"] = start, end
            factors["period_end"] = end_mode
            changed_month += 1
        row["messages"][-2]["content"] = prefix + text
        metadata["version"] = VERSION
        v1.target(row)
        # Explicit changes are limited to a current-month end on two MTD rows.
        after = v1.target(row)
        if family == "relative_quote_month":
            retained_before, retained_after = deepcopy(before), deepcopy(after)
            retained_before["arguments"].pop("date_to")
            retained_after["arguments"].pop("date_to")
            if retained_before != retained_after:
                raise ValueError("Month wording may change only the declared inclusive end")
        elif before != after:
            raise ValueError("Non-month target changed")
        if (row["tools"] != source["tools"] or row["messages"][:-2] != source["messages"][:-2]
                or v1.helper().current_request(row["messages"][-2]["content"])[0] !=
                   v1.helper().current_request(source["messages"][-2]["content"])[0]):
            raise ValueError("Trusted context, permissions or history changed")
    if (len(result), changed_recency, changed_month, month_to_date) != (116, 20, 12, 2):
        raise ValueError("Complete reviewed contrast inventory is required")
    return result


def prepare(source, native, output):
    source, native, output = (Path(p).resolve() for p in (source, native, output))
    if output.exists() or source == output or source in output.parents or not output.parent.is_dir():
        raise ValueError("A new isolated output with an existing parent is required")
    v1 = prior()
    with TemporaryDirectory(prefix="semantic-v2-reference-", dir=output.parent) as temporary:
        reference = Path(temporary) / "v1"
        previous = v1.prepare(source, native, reference)
        if sha((reference / "manifest.json").read_bytes()) != REFERENCE_MANIFEST_SHA256:
            raise ValueError("Exact reviewed v1 preparation changed")
        old_rows = [json.loads(line) for line in (reference / "contrasts.jsonl").read_bytes().splitlines()]
        rows = clarify_rows(old_rows)
        source_raw = (source / "train.jsonl").read_bytes()
        if sha(source_raw) != v1.SOURCE_SHA256["train.jsonl"]:
            raise ValueError("Original replay changed after reference preparation")
        source_rows = [json.loads(line) for line in source_raw.splitlines()]
        valid = (reference / "valid.jsonl").read_bytes()
        development = [json.loads(line) for line in valid.splitlines()]
        v1.validate_exclusions(source_rows, rows, development)
        additions = "".join(v1.encoded(row) + "\n" for row in rows).encode()
        files = {"contrasts.jsonl": additions, "train.jsonl": source_raw + additions, "valid.jsonl": valid}
        manifest = deepcopy(previous)
        manifest.update(
            version=VERSION, generator_sha256=sha(Path(__file__).read_bytes()),
            source_generator_sha256=PRIOR_SHA256,
            prior_preparation_manifest_sha256=REFERENCE_MANIFEST_SHA256,
            status="PREPARED ONLY; semantic review and server preflight pending",
            wording_corrections={"explicit_latest_payment_requests": 20,
                                "explicit_calendar_or_month_to_date_requests": 12,
                                "month_to_date_targets": 2},
            files={name: sha(raw) for name, raw in files.items()})
        output.mkdir(mode=0o700)
        for name, raw in files.items():
            (output / name).write_bytes(raw)
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.native, args.output), indent=2, ensure_ascii=False))
