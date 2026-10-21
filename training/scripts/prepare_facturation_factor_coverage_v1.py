"""Prepare TRAIN-only coverage corrections without loading or training a model."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import date,timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import re

VERSION="facturation-factor-coverage-correction-v1-en-fr"
BASE_SHA="dc0587953e42197d3e1b499af2913c13d94c971a9ced65ec0ab0769adf3f4bad"
SOURCE_SHA="05e792a632ba37cdbb71845e57c0444f4feb4c94851addc5ec84a9674da0cb0d"
VALID_SHA="8deb2bde51e014a8f5cb3c453c700c9a70091850e467aa3c9ab941e788e56487"
HELPER_SHA="3d7f2eee56c328593d8ccfbd01c4aea1e637da0b6a4d13079ee48d5489d27d43"
NAV=(97,111,407,408,409,411,412,413,415,416,417,418)
DATES=(385,386,387,388,389,391,392,393,394,395,396,397,398,399,400,402,403,404,405,406)
REMARKS=(437,438,443,444)
LITERALS=("SYN-Parcel verified","SYN-Records reviewed and ready for release")
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encode(row):return (json.dumps(row,ensure_ascii=False)+"\n").encode()
def rows(raw):return [json.loads(line) for line in raw.splitlines()]
def helper():
    p=Path(__file__).with_name("prepare_facturation_semantic_contrasts_v1.py")
    if sha(p.read_bytes())!=HELPER_SHA:raise ValueError("Reviewed helper changed")
    spec=importlib.util.spec_from_file_location("factor_coverage_helper",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m
def exclusion_envelope(row):
    # Read only input fields. Evaluation targets never enter this envelope.
    source_messages=row["messages"]
    if not source_messages or source_messages[-1]["role"] not in ("user","assistant"):
        raise ValueError("Unsupported exclusion boundary")
    if source_messages[-1]["role"]=="assistant":source_messages=source_messages[:-1]
    if not source_messages or source_messages[-1]["role"]!="user":
        raise ValueError("Exclusion must end at the current user request")
    messages=deepcopy(source_messages)+[{"role":"assistant","content":None}]
    tools=row["offered_tool_schemas"] if "offered_tool_schemas" in row else row["tools"]
    return {"messages":messages,"tools":deepcopy(tools)}
def generated_remarks(source):
    old=helper();result=[]
    for n in REMARKS:
        parent=source[n-1];language=parent["language"]
        original=old.target(parent)["arguments"]
        value=original["changes"]["remarque"]
        prefix,text=old.helper().current_request(parent["messages"][-2]["content"])
        if text.count(value)!=1:raise ValueError("Literal must have one current-request occurrence")
        marker="; set Due date to " if language=="en" else "; mets Date d’échéance au "
        joining=" and set Due date to " if language=="en" else " et mets Date d’échéance au "
        if text.count(marker)!=1:raise ValueError("Expected TRAIN field boundary changed")
        for literal in LITERALS:
            for quoted in (False,True):
                arguments=deepcopy(original);arguments["changes"]["remarque"]=literal
                rendered=json.dumps(literal,ensure_ascii=False) if quoted else literal
                request=text.replace(value,rendered).replace(marker,joining)
                row=old.make(parent,n,"quoted_unquoted_complete_remarks",language,request,arguments,
                    factors={"resource":original["resource"],"quoted":quoted,
                             "literal_words":len(literal.split()),"literal":literal,
                             "separator":"and" if language=="en" else "et"})
                row["augmentation"]["version"]=VERSION
                if row["messages"][-2]["content"]!=prefix+request:raise ValueError("History changed")
                result.append(row)
    return result
def copies(source,raw_lines):
    result=[];payloads=[];provenance=[]
    for n in NAV+DATES:
        row=deepcopy(source[n-1]);raw=raw_lines[n-1]+b"\n"
        if n==111:
            # Verified French request; annotate metadata without changing model input.
            if "Current request: Amène-moi à la page de liste des utilisateurs." not in row["messages"][-2]["content"]:
                raise ValueError("Source111 French request changed")
            row["language"]="fr";raw=encode(row)
        if row["messages"]!=source[n-1]["messages"] or row["tools"]!=source[n-1]["tools"]:
            raise ValueError("Copied model input/target changed")
        result.append(row);payloads.append(raw)
        provenance.append({"source_line":n,"source_raw_sha256":sha(raw_lines[n-1]),
                           "metadata_only_language_annotation":n==111})
    return result,payloads,provenance
def coverage(all_rows,generated):
    old=helper();nav=Counter();boundaries=Counter();styles=Counter()
    for row in all_rows:
        call=old.target(row);args=call["arguments"]
        if row["application"]=="facturation" and call["name"]=="navigate" and args.get("resource") in ("user","users"):
            nav[(row.get("language"),args["resource"])]+=1
        meta=row.get("augmentation",{})
        if meta.get("family")=="date_boundaries":
            mode=meta["factors"]["mode"];boundaries[(row.get("language"),mode)]+=1
            anchor=meta["factors"].get("anchor")
            d=date.fromisoformat(anchor) if anchor else None
            expected={"unbounded":{}}
            if d is not None:
                expected.update(lower_inclusive={"date_from":anchor},
                    lower_exclusive={"date_from":(d+timedelta(days=1)).isoformat()},
                    upper_inclusive={"date_to":anchor},
                    upper_exclusive={"date_to":(d-timedelta(days=1)).isoformat()},
                    closed={"date_from":anchor,"date_to":(d+timedelta(days=6)).isoformat()})
            if mode not in expected or args!=expected[mode]:raise ValueError("Incorrect calendar label")
    for row in generated:
        target=old.target(row)["arguments"];f=row["augmentation"]["factors"]
        literal=target["changes"]["remarque"]
        _,text=old.helper().current_request(row["messages"][-2]["content"])
        if (json.dumps(literal,ensure_ascii=False) in text)!=f["quoted"]:
            raise ValueError("Quotation metadata disagrees with request")
        if text.count(literal)!=1 or len(literal.split())!=f["literal_words"]:
            raise ValueError("Full literal or its length changed")
        styles[(row["language"],target["resource"],f["quoted"],f["literal_words"])]+=1
    expected_nav=Counter({("en","user"):4,("en","users"):3,("fr","user"):3,("fr","users"):4})
    modes=("lower_inclusive","lower_exclusive","upper_inclusive","upper_exclusive","closed","unbounded")
    expected_dates=Counter({(lang,mode):1 if mode=="unbounded" else 2 for lang in ("en","fr") for mode in modes})
    expected_styles=Counter({(lang,res,quoted,length):1 for lang in ("en","fr") for res in ("proforma","quote")
                            for quoted in (False,True) for length in (2,6)})
    if nav!=expected_nav or boundaries!=expected_dates or styles!=expected_styles:
        raise ValueError("Language/action/style/date coverage is incomplete")
    return {"navigation":[{"language":k[0],"resource":k[1],"count":v} for k,v in sorted(nav.items())],
            "date_boundaries":[{"language":k[0],"mode":k[1],"count":v} for k,v in sorted(boundaries.items())],
            "new_literal_factor_cells":len(styles),"all_factor_cells_verified":True}
def sensitive_checks(all_rows):
    pattern=re.compile(r"-----BEGIN .*PRIVATE KEY|\bsk-[A-Za-z0-9]{16,}|id_ed25519|"
                       r"(?:password|api[_ -]?key|access[_ -]?token|secret)\s*[:=]\s*\S+",re.I)
    for row in all_rows:
        text=row["messages"][-2]["content"]+"\n"+json.dumps(row["messages"][-1],ensure_ascii=False)
        if pattern.search(text):raise ValueError("Possible credential in supervised data")
def prepare(base,source,native,output,exclusions=()):
    base,source,native,output=(Path(p).resolve() for p in (base,source,native,output))
    if output.exists() or not output.parent.is_dir() or any(p==output or p in output.parents for p in (base,source,native)):
        raise ValueError("A new isolated output with existing parent is required")
    raw=(base/"train.jsonl").read_bytes();approved=(source/"train.jsonl").read_bytes()
    valid=(base/"valid.jsonl").read_bytes()
    if (sha(raw),sha(approved),sha(valid))!=(BASE_SHA,SOURCE_SHA,VALID_SHA):
        raise ValueError("Pinned TRAIN/validation inputs changed")
    if (source/"valid.jsonl").read_bytes()!=valid or not raw.endswith(b"\n") or not approved.endswith(b"\n"):
        raise ValueError("Source validation or line boundaries changed")
    original,approved_rows=rows(raw),rows(approved)
    if len(original)!=128 or len(approved_rows)!=500:raise ValueError("Whole reviewed inputs required")
    old=helper()
    if {n:sha((native/n).read_bytes()) for n in old.NATIVE_SHA256}!=old.NATIVE_SHA256:
        raise ValueError("Native business contracts changed")
    generated=generated_remarks(approved_rows)
    copied,copied_bytes,provenance=copies(approved_rows,approved.splitlines())
    all_rows=original+generated+copied
    expected=Counter(facturation=144,management_projet=16,design_workflow=16)
    if len(all_rows)!=176 or Counter(r["application"] for r in all_rows)!=expected:raise ValueError("Replay quotas changed")
    excluded=[exclusion_envelope(r) for r in rows(valid)]
    exclusion_hashes={}
    for ordinal,path in enumerate(exclusions):
        path=Path(path);payload=path.read_bytes()
        excluded.extend(exclusion_envelope(r) for r in rows(payload))
        exclusion_hashes[f"{ordinal:02d}-{path.name}"]=sha(payload)
    old.validate_exclusions(original+copied,generated,excluded)
    prior=old.helper()
    source_keys={prior.canonical_input_key(r) for r in approved_rows}
    if any(prior.canonical_input_key(r) in source_keys for r in generated):
        raise ValueError("Generated example duplicates approved TRAIN")
    sensitive_checks(all_rows)
    factors=coverage(all_rows,generated)
    if Counter(r["language"] for r in generated+copied)!=Counter(en=24,fr=24):
        raise ValueError("Added EN/FR balance changed")
    additions=b"".join(encode(r) for r in generated)+b"".join(copied_bytes)
    train=raw+additions
    if rows(train)!=all_rows:raise ValueError("Serialization changed data")
    files={"train.jsonl":train,"valid.jsonl":valid,"additions.jsonl":additions}
    manifest={"version":VERSION,"status":"PREPARED ONLY; numerical preflight and review required",
        "languages":["en","fr"],"applications":["facturation","management_projet","design_workflow"],
        "count":176,"by_application":dict(expected),"base128_preserved_byte_for_byte":True,
        "additions":{"new_remarks":16,"navigation":12,"date_boundaries":20,"languages":{"en":24,"fr":24}},
        "source_sha256":{"base_train":BASE_SHA,"approved500_train":SOURCE_SHA,"valid":VALID_SHA},
        "native_contract_sha256":old.NATIVE_SHA256,"copied_source_rows":provenance,
        "generated_source_rows":list(REMARKS),"coverage":factors,
        "exclusion_input_rows_checked":len(excluded),"extra_exclusion_sha256":exclusion_hashes,
        "evaluation_targets_used_for_training":False,"sensitive_supervised_rows_checked":176,
        "generator_sha256":sha(Path(__file__).read_bytes()),"helper_sha256":HELPER_SHA,
        "files":{n:sha(b) for n,b in files.items()},"training_executed":False,
        "model_accepted":False,"production_activation":False}
    output.mkdir(mode=0o700)
    for name,payload in files.items():(output/name).write_bytes(payload)
    (output/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n")
    return manifest
if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("base","source","native","output"):p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--exclusion",action="append",type=Path,default=[])
    a=p.parse_args();print(json.dumps(prepare(a.base,a.source,a.native,a.output,a.exclusion),indent=2))
