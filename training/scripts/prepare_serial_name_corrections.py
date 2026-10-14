"""Prepare corrected Contracts retention, conditional on actual R8 acceptance.

No model binding, training or acceptance is created by this command.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from serial_scope_v3 import DECLARATION, SOURCE_SHA256, reviewed_prefix, validate_retained_curriculum

ROOT = Path(__file__).resolve().parents[2]
SOURCE = 'shared-v6r9-en-fr'
OUTPUT = 'shared-v6r10-en-fr'
SOURCE_MANIFEST = '2502245524902f6e5c193c783030d239d5cadaddf5b20dd535bf417d0272d2c1'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def assemble():
    source = ROOT / 'training/datasets' / SOURCE
    raw = (source / 'manifest.json').read_bytes()
    if digest(raw) != SOURCE_MANIFEST:
        raise ValueError('Reviewed Contracts preparation changed')
    prior = json.loads(raw)
    parent = ROOT / 'training/datasets' / prior['retained_dataset']['version']
    prefix_manifest, prefix = reviewed_prefix(ROOT)
    original = (parent / 'train.jsonl').read_bytes()
    payloads = {name: (source / name).read_bytes() for name in ('train.jsonl', 'valid.jsonl')}
    if any(digest(raw) != prior['files'][name] for name, raw in payloads.items()):
        raise ValueError('Reviewed Contracts split changed')
    if digest(original) != prior['retained_dataset']['files']['train.jsonl']:
        raise ValueError('Original R8 curriculum changed')
    if not payloads['train.jsonl'].startswith(original):
        raise ValueError('Prior preparation lost the original retained prefix')
    payloads['train.jsonl'] = prefix['train.jsonl'] + payloads['train.jsonl'][len(original):]
    manifest = deepcopy(prior)
    manifest.update(
        version=OUTPUT,
        generator_sha256=digest(Path(__file__).read_bytes()),
        scope_validator_sha256=SOURCE_SHA256['serial_scope_v3.py'],
        scope_dependencies=SOURCE_SHA256,
        source_preparation={'version': SOURCE, 'manifest_sha256': SOURCE_MANIFEST},
        retained_corrections=dict(DECLARATION),
        files={name: digest(raw) for name, raw in payloads.items()},
        split_policy='Bind the actual R8 predecessor dataset and replace exactly six reviewed targets in its retained training prefix. Preserve all other retained rows, validation, evaluation and original Contracts-only additions. No general retention exception is permitted.',
        training_status='PREPARATION ONLY, CONDITIONAL ON R8 ACCEPTANCE. An untrained corrected prefix is not an accepted predecessor. Require actual accepted R8 model/run binding, fresh baseline, server numerical/export rehearsal and resource gates before training.',
        model_binding={'status': 'UNBOUND; active R8 results pending',
                       'accepted_predecessor_required': 'The actual R8 run with its original recorded dataset and model artifacts, not the untrained V5r9 preparation.'},
        native_correction_evidence={'corrected_prefix_manifest_sha256': DECLARATION['prefix_manifest_sha256'],
                                    'native_metadata': prefix_manifest['native_metadata']})
    validate_retained_curriculum('contrat', manifest, payloads['train.jsonl'], payloads['valid.jsonl'], parent, correction_root=ROOT)
    return payloads, manifest


def prepare():
    output = ROOT / 'training/datasets' / OUTPUT
    if output.exists():
        raise ValueError('Never overwrite a versioned cumulative preparation')
    payloads, manifest = assemble()
    output.mkdir()
    for name, raw in payloads.items():
        with (output / name).open('xb') as stream:
            stream.write(raw)
    with (output / 'manifest.json').open('x') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    return manifest


if __name__ == '__main__':
    result = prepare()
    print(json.dumps({'version': result['version'], 'counts': result['counts'],
                      'held_out': result['held_out_count'], 'training_started': False,
                      'model_acceptance_verified': False}))
