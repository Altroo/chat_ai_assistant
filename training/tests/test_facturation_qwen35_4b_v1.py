"""Prevent ambiguous entity roles and evaluation leakage in the4B TRAIN correction."""
import json,re,sys,unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"training/scripts"))
import prepare_facturation_qwen35_4b_v1 as preparation

class RoleCorrectionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.folder=ROOT/"training/datasets/facturation-focus-v2-en-fr"
  cls.original=[json.loads(l)for l in(cls.folder/"train.jsonl").read_text().splitlines()]
  cls.manifest=json.loads((cls.folder/"manifest.json").read_text())
 def test_repair_changes_only_ambiguous_user_inputs(self):
  fixed=preparation.repaired(self.original)
  self.assertEqual([i for i,(a,b)in enumerate(zip(self.original,fixed))if a!=b],[18,19])
  for i in(18,19):
   self.assertEqual(self.original[i]["messages"][0],fixed[i]["messages"][0])
   self.assertEqual(self.original[i]["messages"][-1],fixed[i]["messages"][-1])
   self.assertEqual(self.original[i]["tools"],fixed[i]["tools"])
   before=self.original[i]["messages"][-2]["content"].split("Current request: ")[0]
   self.assertTrue(fixed[i]["messages"][-2]["content"].startswith(before+"Current request: "))
  self.assertIn("customer SYN-Aster",fixed[18]["messages"][-2]["content"])
  self.assertIn("product SYN-PIGMENT",fixed[18]["messages"][-2]["content"])
  self.assertIn("client SYN-Aster",fixed[19]["messages"][-2]["content"])
  self.assertIn("article SYN-PIGMENT",fixed[19]["messages"][-2]["content"].replace("’",""))
 def test_repair_refuses_changed_source_target(self):
  altered=deepcopy(self.original)
  preparation.target(altered[18])["arguments"]["client_name"]="SYN-Wrong"
  with self.assertRaises(AssertionError):preparation.repaired(altered)
 def test_labels_follow_explicit_roles_and_not_capitalization(self):
  examples=preparation.additions(self.original)
  self.assertEqual(len(examples),16)
  self.assertEqual(sum(r["language"]=="en"for r in examples),8)
  for row in examples:
   text=row["messages"][-2]["content"]
   product=re.search(r"(?:product|item|article|produit)\s+«([^»]+)»",text)
   customer=re.search(r"(?:customer(?: must be)?|client(?: doit être)?)\s+«([^»]+)»",text)
   self.assertIsNotNone(product,text);self.assertIsNotNone(customer,text)
   args=preparation.target(row)["arguments"]
   self.assertEqual(args["product_name"],product.group(1))
   self.assertEqual(args["client_name"],customer.group(1))
   self.assertLess(product.start(),customer.start())
   self.assertEqual(args.get("unpaid",False),"unpaid" in text or "impayées" in text)
   self.assertFalse(set(args)&{"date_from","date_to","identifier","invoice_number"})
 def test_frozen_validation_cannot_be_added_to_train(self):
  row=json.loads((self.folder/"valid.jsonl").read_text().splitlines()[0])
  with self.assertRaises(ValueError):preparation.exclusions(self.manifest,[row])
 def test_changed_exclusion_input_is_rejected(self):
  original=Path.read_bytes
  shared=preparation.ROOT/preparation.SHARED_VALID
  def read(path):
   return b"" if path==shared else original(path)
  with patch.object(Path,"read_bytes",read):
   with self.assertRaisesRegex(ValueError,"Reviewed exclusion input changed"):
    preparation.exclusions(self.manifest,[])
 def test_changed_shared_dependency_is_rejected(self):
  original=Path.read_bytes
  changed=preparation.ROOT/"src/chat_ai_assistant/routing.py"
  def read(path):
   return original(path)+b"\\n# changed" if path==changed else original(path)
  with patch.object(Path,"read_bytes",read):
   with self.assertRaisesRegex(ValueError,"Reviewed dependency changed"):
    preparation.dependencies(self.manifest)
 def test_all_parent_dependency_pins_are_retained(self):
  pins=preparation.dependencies(self.manifest)
  self.assertTrue(self.manifest["helper_sha256"].items()<=pins.items())
  self.assertEqual(pins[preparation.GUARD_PATH],preparation.GUARD_SHA)
 def test_generated_data_preserves_frozen_rows_and_labels(self):
  prepared=ROOT/"training/datasets"/preparation.VERSION
  old=(self.folder/"train.jsonl").read_bytes().splitlines(keepends=True)
  new=(prepared/"train.jsonl").read_bytes().splitlines(keepends=True)
  self.assertEqual(len(new),1503)
  self.assertEqual([i for i in range(1487)if old[i]!=new[i]],[18,19])
  self.assertEqual((self.folder/"valid.jsonl").read_bytes(),(prepared/"valid.jsonl").read_bytes())
  for a,b in zip(old,new):self.assertEqual(preparation.target(json.loads(a)),preparation.target(json.loads(b)))
if __name__=="__main__":unittest.main()
