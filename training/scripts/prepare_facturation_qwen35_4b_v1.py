"""Prepare reviewed Facturation role contrasts for the new shared model.
Synthetic TRAIN inputs only; no model, database, or business operations.
"""
import argparse,hashlib,json,os,subprocess,sys
from collections import Counter
from copy import deepcopy
from pathlib import Path
from jsonschema import validate
import prepare_facturation_argument_coverage_v2 as guard
from prepare_shared_v5r8 import SECRET,context,native_check

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/"training/datasets/facturation-focus-v2-en-fr"
VERSION="facturation-qwen35-4b-v1-en-fr"
PARENT_SHA="b5e9850bd8bcd7a2090f618b60e9d5bdc0a4f1e015a5f744fafdb64305c1cc8b"
SHARED_VALID="training/datasets/shared-v5r11-en-fr/valid.jsonl"
SHARED_VALID_SHA="8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487"
GUARD_PATH="training/scripts/prepare_facturation_argument_coverage_v2.py"
GUARD_SHA="9eb330e0293e3a65d14e762418bc8e1b991a57ca563d55c48274017e40d896ae"
SCENARIOS=(
 ("search_invoices",None,"invoices","factures",False),
 ("search_invoices",None,"unpaid invoices","factures impayées",True),
 ("search_quotes",None,"quotes","devis",False),
 ("search_quotes",None,"quotations","devis",False),
 ("search_documents","proforma","pro forma invoices","factures pro forma",False),
 ("search_documents","credit_note","credit notes","factures d’avoir",False),
 ("search_documents","delivery_note","delivery notes","bons de livraison",False),
 ("search_payments",None,"payments","règlements",False),
)
NAMES=(
 ("SYN-Atelier-541","SYN-MODULE-573"),("SYN-DELTA-582","SYN-Lampe-519"),
 ("SYN-Noria-621","SYN-Noria-642"),("SYN-PIVOT-683","SYN-Orme-674"),
 ("SYN-Boreal-719","SYN-BOREAL-732"),("SYN-CADRE-763","SYN-Aurore-751"),
 ("SYN-Sillage-804","SYN-TRAME-827"),("SYN-ARDOISE-869","SYN-Mistral-843"),
)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def dependencies(manifest):
 pins={**manifest["helper_sha256"],GUARD_PATH:GUARD_SHA}
 for name,digest in pins.items():
  if sha((ROOT/name).read_bytes())!=digest:raise ValueError("Reviewed dependency changed: "+name)
 return pins

def target(row):return row["messages"][-1]["tool_calls"][0]["function"]
def encoded(rows):return "".join(json.dumps(r,ensure_ascii=False)+"\n" for r in rows).encode()
def repaired(parent):
 rows=deepcopy(parent)
 changes=(
  (18,"Filter invoices for customer SYN-Aster containing product SYN-PIGMENT, January 2027, with an unpaid balance."),
  (19,"Filtre les factures du client SYN-Aster contenant l’article SYN-PIGMENT, janvier 2027, avec un solde impayé."),
 )
 for index,text in changes:
  original=rows[index]["messages"][-2]["content"]
  prefix=original[:original.index("Current request: ")+len("Current request: ")]
  assert target(rows[index])=={"name":"search_invoices","arguments":{"client_name":"SYN-Aster","product_name":"SYN-PIGMENT","unpaid":True,"date_from":"2027-01-01","date_to":"2027-01-31"}}
  rows[index]["messages"][-2]["content"]=prefix+text
 return rows
def additions(parent):
 result=[]
 for i,(tool,resource,en_label,fr_label,unpaid) in enumerate(SCENARIOS):
  template=next(r for r in parent if target(r)["name"]==tool and
   (resource is None or target(r)["arguments"].get("resource")==resource))
  customer,product=NAMES[i]
  for lang in ("en","fr"):
   row=deepcopy(template);trusted=context(row)
   trusted.update(current_resource=None,current_identifier=None,current_invoice_id=None,
    previous_result_type=None,previous_result_count=0,previous_result_identifiers=[],
    interface_language="fr" if lang=="en" else"en")
   trusted.pop("shortcut_search_hint",None)
   row["messages"][0]["content"]=row["messages"][0]["content"].split("Trusted context: ",1)[0]+"Trusted context: "+json.dumps(trusted,ensure_ascii=False)
   if i%2==0:
    text=(f"With product «{product}» as the item filter, find {en_label} for customer «{customer}»."
     if lang=="en" else f"Avec l’article «{product}» comme filtre produit, retrouve les {fr_label} du client «{customer}».")
   else:
    text=(f"I am looking for {en_label} containing item «{product}»; the customer must be «{customer}»."
     if lang=="en" else f"Je recherche les {fr_label} contenant le produit «{product}»; le client doit être «{customer}».")
   arguments={"client_name":customer,"product_name":product}
   if resource:arguments={"resource":resource,**arguments}
   if unpaid:arguments["unpaid"]=True
   row["messages"]=[row["messages"][0],{"role":"user","content":text},
    {"role":"assistant","content":None,"tool_calls":[{"type":"function","function":{"name":tool,"arguments":arguments}}]}]
   row.update(application="facturation",language=lang,capability_profile="member_read",
    curriculum_category="explicit_product_first_roles",contrast={"scenario":i,"product_first":True,"names_rely_on_explicit_roles":True})
   result.append(row)
 return result
def exclusions(manifest,changed):
 held={}
 for mapping in(manifest["held_out"],manifest["historical_regression_held_out"],manifest["fresh_controls"]["files"]):
  for name,item in mapping.items():
   if name in held:assert held[name]==item["sha256"]
   held[name]=item["sha256"]
 excluded=[];seen=set()
 for name,digest in held.items():
  raw=(ROOT/name).read_bytes();assert sha(raw)==digest
  if digest in seen:continue
  seen.add(digest)
  excluded.extend(guard.input_only(json.loads(line)) for line in raw.splitlines())
 validation_inputs={str((PARENT/"valid.jsonl").relative_to(ROOT)):manifest["files"]["valid.jsonl"],SHARED_VALID:SHARED_VALID_SHA}
 for name,digest in validation_inputs.items():
  raw=(ROOT/name).read_bytes()
  if sha(raw)!=digest:raise ValueError("Reviewed exclusion input changed: "+name)
  excluded.extend(guard.input_only(json.loads(line)) for line in raw.splitlines())
 parent=[json.loads(l)for l in(PARENT/"train.jsonl").read_bytes().splitlines()]
 return guard.exclusions(parent,changed,excluded)
def prepare(backend,interpreter,output):
 if output.exists():raise ValueError("Never overwrite a versioned training dataset")
 parent_manifest_raw=(PARENT/"manifest.json").read_bytes();assert sha(parent_manifest_raw)==PARENT_SHA
 manifest=json.loads(parent_manifest_raw);helper_pins=dependencies(manifest)
 raws={n:(PARENT/n).read_bytes()for n in("train.jsonl","valid.jsonl")}
 assert all(sha(raw)==manifest["files"][n]for n,raw in raws.items())
 parent=[json.loads(l)for l in raws["train.jsonl"].splitlines()]
 assert len(parent)==1487 and len(raws["valid.jsonl"].splitlines())==133
 for name,digest in manifest["native_metadata"]["facturation"].items():
  assert sha((backend/name).read_bytes())==digest,name
 fixed=repaired(parent);draft=additions(parent)
 changed=[fixed[i]for i in(18,19)]+draft
 if SECRET.search(encoded(changed).decode()):raise ValueError("Sensitive or unsupported-language content")
 for row in changed:
  action=target(row);offered={t["function"]["name"]:t["function"]["parameters"]for t in row["tools"]}
  validate(action["arguments"],offered[action["name"]])
 overlap=exclusions(manifest,changed)
 # Recompute the real permission shortlist for new examples. Corrected legacy
 # inputs keep their original context/tools; validation uses a read-only profile.
 native_input=deepcopy(changed)
 for row in native_input:row["capability_profile"]="member_read"
 env={**os.environ,"PYTHONPATH":os.pathsep.join((str(ROOT/"src"),str(ROOT/"training/scripts"))),"PYTHONDONTWRITEBYTECODE":"1"}
 command=[str(interpreter),"-B",str(Path(__file__).resolve()),"--native-check","--backend",str(backend)]
 checked=subprocess.run(command,input=json.dumps(native_input),text=True,capture_output=True,env=env)
 if checked.returncode:raise RuntimeError("Native metadata validation failed: "+checked.stderr[-2500:])
 native=json.loads(checked.stdout);verified=native["rows"]
 assert len(verified)==18
 for original,checked_row in zip(changed,verified):
  assert target(original)==target(checked_row)
  assert original["messages"][-2]==checked_row["messages"][-2]
 draft=verified[2:]
 lines=raws["train.jsonl"].splitlines(keepends=True)
 assert all(line.endswith(b"\n")for line in lines)
 for index in(18,19):lines[index]=encoded([fixed[index]])
 train=b"".join(lines)+encoded(draft)
 assert len(train.splitlines())==1503 and all(lines[i]==raws["train.jsonl"].splitlines(keepends=True)[i] for i in range(1487)if i not in(18,19))
 summary={"version":VERSION,"applications":["facturation"],"languages":["en","fr"],
  "status":"PREPARATION ONLY; no model training or acceptance","source_dataset":"facturation-focus-v2-en-fr",
  "source_manifest_sha256":PARENT_SHA,"generator_sha256":sha(Path(__file__).read_bytes()),
  "helper_sha256":helper_pins,
  "additional_exclusion_inputs":{SHARED_VALID:SHARED_VALID_SHA},
  "counts":{"train":1503,"valid":133,"unchanged_source_train_rows":1485,"clarified_source_train_rows":2,"added":16,"added_by_language":{"en":8,"fr":8},"native_metadata_checked":18},
  "clarified_source_lines":[19,20],"target_labels_changed":False,
  "native_metadata":{"facturation":native["native_sha256"]},"exclusions":overlap,
  "held_out":manifest["held_out"],"historical_regression_held_out":manifest["historical_regression_held_out"],"fresh_controls":manifest["fresh_controls"],
  "files":{"train.jsonl":sha(train),"valid.jsonl":sha(raws["valid.jsonl"])},
  "training_policy":"Measure the 4B baseline and CPU capacity. Prepare a reviewed axis-balanced bounded pilot before any longer run. No automatic production activation.",
  "limitations":["Existing TRAIN includes repeated neutral-history coverage; no claim of 1503 independent scenarios.",
   "Two ambiguous role inputs are clarified; 16 source-grounded bilingual examples vary explicit role order and synthetic name shapes.",
   "Validation bytes and frozen evaluation labels are unchanged. Input-only exclusions do not establish semantic independence.",
   "Metadata/schema checks do not prove authorization, numerical learning or model accuracy."]}
 for name,digest in native["native_sha256"].items():assert sha((backend/name).read_bytes())==digest
 assert (PARENT/"manifest.json").read_bytes()==parent_manifest_raw
 assert dependencies(manifest)==helper_pins
 assert sha((ROOT/SHARED_VALID).read_bytes())==SHARED_VALID_SHA
 output.mkdir()
 (output/"train.jsonl").write_bytes(train);(output/"valid.jsonl").write_bytes(raws["valid.jsonl"])
 (output/"manifest.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n")
 return summary
if __name__=="__main__":
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--backend",type=Path,required=True)
 p.add_argument("--backend-python",type=Path);p.add_argument("--output",type=Path,default=ROOT/"training/datasets"/VERSION)
 p.add_argument("--native-check",action="store_true");a=p.parse_args()
 if a.native_check:
  parent_raw=(PARENT/"manifest.json").read_bytes();assert sha(parent_raw)==PARENT_SHA
  dependencies(json.loads(parent_raw))
  print(json.dumps(native_check("facturation",a.backend,json.load(sys.stdin)),ensure_ascii=False))
 else:
  if not a.backend_python:p.error("--backend-python is required")
  print(json.dumps(prepare(a.backend,a.backend_python,a.output)["counts"]))
