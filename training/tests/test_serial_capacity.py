"""Verify capacity startup rejects wrong stages before importing model libraries."""
import builtins
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'training/scripts'))

class BeforeWeights(Exception):pass

class SerialCapacityStartupTests(unittest.TestCase):
    def start(self, stage, version, retained, *, platform='Linux', server='1'):
        original=builtins.__import__
        def bounded(name,*args,**kwargs):
            if name in ('torch','transformers','psutil'):raise BeforeWeights
            return original(name,*args,**kwargs)
        with tempfile.TemporaryDirectory() as directory:
            args=['probe_cpu_serial_v1.py','--stage',stage,'--retained-data',str(ROOT/'training/datasets'/retained),
                  '--data',str(ROOT/'training/datasets'/version),'--model',str(Path(directory)/'unused'),
                  '--output',str(Path(directory)/'unused.json')]
            with patch.object(sys,'argv',args),patch('platform.system',return_value=platform), \
                 patch.dict(os.environ,{'CHAT_AI_TRAINING_SERVER':server}),patch('builtins.__import__',side_effect=bounded):
                runpy.run_path(str(ROOT/'training/scripts/probe_cpu_serial_v1.py'),run_name='__main__')
    def test_each_stage_reaches_weight_boundary_with_exact_predecessor(self):
        for stage,n in [('contrat',6),('gestion_magasin',7),('reservation',8)]:
            with self.subTest(stage=stage),self.assertRaises(BeforeWeights):
                self.start(stage,f'shared-v{n}r6-en-fr',f'shared-v{n-1}r6-en-fr')
    def test_missing_refinement_or_skipped_stage_rejects_before_weights(self):
        for stage,previous in [('contrat','shared-v5r5-en-fr'),('reservation','shared-v5r6-en-fr')]:
            with self.subTest(stage=stage,previous=previous),self.assertRaises(SystemExit):
                self.start(stage,'shared-v6r6-en-fr',previous)
    def test_server_only_guard(self):
        for platform,flag in [('Darwin','1'),('Linux','0')]:
            with self.subTest(platform=platform,flag=flag),self.assertRaisesRegex(SystemExit,'approved Linux server'):
                self.start('contrat','shared-v6r6-en-fr','shared-v5r6-en-fr',platform=platform,server=flag)
