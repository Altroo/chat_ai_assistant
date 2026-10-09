"""Combine only declared approved application synthetic SFT sources.
All independent held-out sets stay outside training/validation. No database access.
"""
import argparse,hashlib,json,re,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCES={'facturation':'facturation-v4-en-fr','management_projet':'management-projet-v1-en-fr'}
parser=argparse.ArgumentParser();parser.add_argument('--include-design-workflow',action='store_true');args=parser.parse_args()
if args.include_design_workflow:SOURCES['design_workflow']='design-workflow-v1-en-fr'
version='shared-v2-en-fr' if args.include_design_workflow else 'shared-v1-en-fr'
OUT=ROOT/'training/datasets'/version
SECRET=re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:Bearer\s+)[A-Za-z0-9._-]{16,}|(?:password|api[_-]?key|secret|access[_-]?token)\s*[:=]\s*\S+',re.I)
held={}
for app,source in SOURCES.items():
    dataset='facturation-acceptance-en-fr' if app=='facturation' else source
    path=ROOT/'training/datasets'/dataset/'test.eval.jsonl'
    held[app]=[json.loads(line) for line in path.read_text().splitlines()]
def key(app,prompt):return app+':'+re.sub(r'\W+',' ',unicodedata.normalize('NFKD',prompt).casefold()).strip()
held_keys={key(app,row['messages'][-1]['content']) for app,rows in held.items() for row in rows}
OUT.mkdir(parents=True,exist_ok=True);counts={};source_hashes={};split_keys={}
for name in ['train.jsonl','valid.jsonl']:
    combined=[];keys=set()
    for app,dataset in SOURCES.items():
        path=ROOT/'training/datasets'/dataset/name
        source_hashes[app+'/'+name]=hashlib.sha256(path.read_bytes()).hexdigest()
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        for row in rows:
            if SECRET.search(json.dumps(row,ensure_ascii=False)):raise ValueError('Sensitive source input')
            prompt=next(m['content'] for m in reversed(row['messages']) if m['role']=='user')
            candidate=key(app,prompt)
            if candidate in keys or candidate in held_keys:raise ValueError('Duplicate or held-out prompt in SFT source')
            keys.add(candidate);combined.append({**row,'application':app})
        counts[app+'/'+name]=len(rows)
    split_keys[name]=keys
    (OUT/name).write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in combined))
if split_keys['train.jsonl']&split_keys['valid.jsonl']:raise ValueError('Cross-split prompt overlap')
manifest={'version':version.replace('shared-','shared-synthetic-'),'applications':list(SOURCES),'languages':['en','fr'],'source':'Approved versioned synthetic sources only. No confidential business records or conversation data.','sources':source_hashes,'counts':counts,'held_out_exclusion':'All declared independent application acceptance sets excluded by normalized application/prompt key. Per-application near-duplicate limitations remain as stated in their source manifests.','training_policy':'Continue from the retained Facturation v4 merged checkpoint. Alternate application samples using --balanced-applications; record actual steps and exposure in training provenance. No candidate is automatically activated.','files':{name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['train.jsonl','valid.jsonl']}}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(counts))
