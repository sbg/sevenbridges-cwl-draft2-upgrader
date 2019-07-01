from sbg_cwl_upgrader.converter.cwl_converter import CWLConverterFacade
import json
from unittest import TestCase
import os
import subprocess
import sys
import random
import string


class TestCWLConverter(TestCase):
    def test_all_steps(self):
        with open(os.path.join(os.path.dirname(__file__),
                               'wes_draft2.json'), 'r') as f:
            in_data = json.load(f)
        with open(os.path.join(os.path.dirname(__file__),
                               'wes_cwl1.json'), 'r') as f:
            result = json.load(f)
        c = object.__new__(CWLConverterFacade)
        converted = c._parse(in_data)
        for cwl_key in ['hints', 'steps', 'inputs', 'outputs', 'requirements']:
            self.assertEqual(len(converted[cwl_key]),
                             len(result[cwl_key]),
                             "Number of items in {} not good".format(cwl_key))

    def test_mini_wf(self):
        with open(os.path.join(os.path.dirname(__file__),
                               'mini_wf_d2.cwl'), 'r') as f:
            in_data = json.load(f)
        c = object.__new__(CWLConverterFacade)
        converted = c._parse(in_data)
        v1_file = os.path.join(
            os.path.dirname(__file__),
            'mini_wf_cwl1_{}.cwl'.format(
                ''.join(random.sample(string.ascii_lowercase, 3))
            )
        )
        with open(v1_file, 'w') as f:
            json.dump(converted, f)

        process = subprocess.Popen(
            [sys.executable, "-m", "cwltool", v1_file, "--input", "foo"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, _ = process.communicate()
        os.remove(v1_file)

        self.assertEqual(process.returncode, 0)
        self.assertIn("foo foo", str(stdout))
