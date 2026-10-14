"""Serial retention with one pinned six-target correction for an accepted R8 base.

This validates dataset lineage only. The launcher must separately verify the
actual predecessor model/run acceptance and bind its artifacts before training.
No general modified-retention option exists; V2 remains unchanged.
"""
import hashlib
import json
from pathlib import Path

DEPENDENCIES = {
    'serial_scope_v2.py': '459dab06b7b5dbb6c4d101c3f1d1eba1728593f5f346d444a6f70ea2091c6344',
    'prepare_management_name_errata.py': '1545d5c4dd5c5c252ea13191d6d9d15f523f9ff5eebc46c69c42b03396d8afa3',
    'prepare_management_name_errata_v2.py': '110d912942964b870766afa0c3ed57338effd7da8b40114f25f9440ffa913412',
}
SOURCE_SHA256 = {**DEPENDENCIES, Path(__file__).name: hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def verify_sources():
    for name, expected in SOURCE_SHA256.items():
        if digest(Path(__file__).with_name(name).read_bytes()) != expected:
            raise ValueError('Retained-correction source changed: ' + name)


verify_sources()
from serial_scope_v2 import BASE_APPLICATIONS, STAGES, validate_stage
from serial_scope_v2 import validate_retained_curriculum as strict_retention
from prepare_management_name_errata_v2 import check_labels

R8_MANIFEST = '56f803ca7110ae78bc53c4a208a7dc7456819c024dc588109da46d7fb1520738'
DECLARATION = {
    'version': 'management-name-errata-v2-en-fr',
    'manifest_sha256': '1ebded1f21cca3921b6e03339df65441255c5d2a883e4241d06028643ad4d0ec',
    'prefix_version': 'shared-v5r9-en-fr',
    'prefix_manifest_sha256': '74fb992ed98e326ff518cdd4302f36205230c41c3b41b34515ef0c823b2763e5',
}


def checked_manifest(directory, expected):
    raw = (directory / 'manifest.json').read_bytes()
    if digest(raw) != expected:
        raise ValueError('Pinned retained-correction manifest changed')
    return json.loads(raw)


def reviewed_prefix(artifacts_root):
    """Read only the exact already-reviewed corrected artifact, never regenerate it."""
    root = Path(artifacts_root)
    if not root.is_dir():
        raise ValueError('Correction artifact root is unavailable')
    prefix = root / 'training/datasets' / DECLARATION['prefix_version']
    manifest = checked_manifest(prefix, DECLARATION['prefix_manifest_sha256'])
    errata = root / 'training/datasets' / DECLARATION['version']
    correction = checked_manifest(errata, DECLARATION['manifest_sha256'])
    if manifest['parent_manifest_sha256'] != R8_MANIFEST or correction['parent_manifest_sha256'] != R8_MANIFEST:
        raise ValueError('Unexpected correction parent')
    payloads = {name: (prefix / name).read_bytes() for name in ('train.jsonl', 'valid.jsonl')}
    if any(digest(raw) != manifest['files'][name] for name, raw in payloads.items()):
        raise ValueError('Reviewed corrected prefix changed')
    raw = (errata / 'train.replacements.jsonl').read_bytes()
    if digest(raw) != correction['files']['train.replacements.jsonl']:
        raise ValueError('Reviewed replacement rows changed')
    return manifest, payloads


def require_preserved_evaluations(current, prefix, artifacts_root):
    """Retain original/fresh exclusions without sending their targets to training."""
    for group in ('held_out', 'historical_regression_held_out'):
        for name, info in prefix[group].items():
            if current.get(group, {}).get(name) != info:
                raise ValueError('Retained evaluation metadata changed')
            if digest((Path(artifacts_root) / name).read_bytes()) != info['sha256']:
                raise ValueError('Frozen evaluation bytes changed')
    if current.get('fresh_controls') != prefix['fresh_controls']:
        # The wording may differ between older manifests; the frozen identities may not.
        value = current.get('fresh_controls', {})
        if any(value.get(key) != prefix['fresh_controls'][key] for key in ('manifest_sha256', 'files')):
            raise ValueError('Fresh-control identity changed')
    if current.get('held_out_count') != sum(info['count'] for info in current.get('held_out', {}).values()):
        raise ValueError('Evaluation count disagrees with its declared cases')


def validate_retained_curriculum(stage, current_manifest, train_payload, valid_payload, retained_directory, *, correction_root=None):
    verify_sources()
    train, valid = [list(map(json.loads, raw.splitlines())) for raw in (train_payload, valid_payload)]
    validate_stage(stage, current_manifest, train, valid, complete_epochs=1)
    for name, raw in (('train.jsonl', train_payload), ('valid.jsonl', valid_payload)):
        if digest(raw) != current_manifest.get('files', {}).get(name):
            raise ValueError('Current split disagrees with its manifest')
    if current_manifest.get('scope_validator_sha256') != SOURCE_SHA256[Path(__file__).name]:
        raise ValueError('Current preparation must bind this scope validator')

    if 'retained_corrections' not in current_manifest:
        if correction_root is not None:
            raise ValueError('Correction root requires an explicit correction declaration')
        result = strict_retention(stage, current_manifest, train_payload, valid_payload, retained_directory)
        mode = 'exact retained bytes'
    else:
        if stage != 'contrat' or current_manifest['retained_corrections'] != DECLARATION:
            raise ValueError('Only the pinned six-target R8-to-Contracts correction is allowed')
        if correction_root is None:
            raise ValueError('Explicit correction artifact root is required')
        retained_directory = Path(retained_directory)
        parent = checked_manifest(retained_directory, R8_MANIFEST)
        prefix_manifest, prefix = reviewed_prefix(correction_root)
        original = {name: (retained_directory / name).read_bytes() for name in ('train.jsonl', 'valid.jsonl')}
        if any(digest(raw) != parent['files'][name] for name, raw in original.items()):
            raise ValueError('Actual R8 retained split changed')
        if prefix['valid.jsonl'] != original['valid.jsonl']:
            raise ValueError('Corrections may not alter validation')
        if not train_payload.startswith(prefix['train.jsonl']):
            raise ValueError('Current stage must retain exactly the reviewed corrected prefix')
        # Reuse every existing V2 stage, manifest, original split and appended-app
        # guard against the actual R8 dataset. Only this proven prefix is substituted.
        restored = original['train.jsonl'] + train_payload[len(prefix['train.jsonl']):]
        result = strict_retention(stage, current_manifest, restored, valid_payload, retained_directory)
        require_preserved_evaluations(current_manifest, prefix_manifest, correction_root)
        result['corrections'] = {
            **DECLARATION,
            'original_training_sha256': parent['files']['train.jsonl'],
            'corrected_training_prefix_sha256': prefix_manifest['files']['train.jsonl'],
            'replaced_targets': 6,
            'unchanged_training_rows': 2333,
            'validation_unchanged': True,
        }
        mode = 'six pinned target replacements; remaining retained bytes exact'

    check_labels(train)
    verify_sources()
    result.update(retention_mode=mode, scope_sources=dict(SOURCE_SHA256),
                  model_acceptance_verified=False, training_authorized=False)
    return result
