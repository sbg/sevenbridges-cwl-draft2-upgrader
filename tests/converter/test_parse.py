from sbg_cwl_upgrader.converter.cwl_converter import CWLConverterFacade
import json
from unittest import TestCase
import os


class TestCWLConverter(TestCase):
    def test_all_steps(self):
        with open(os.path.join(os.path.dirname(__file__),
                               'wes_draft2.json'), 'r') as f:
            in_data = json.load(f)
        with open(os.path.join(os.path.dirname(__file__),
                               'wes_cwl1.json'), 'r') as f:
            result = json.load(f)
        c = object.__new__(CWLConverterFacade)
        self.assertEqual(len(c._parse(in_data)['steps']),
                         len(result['steps']),
                         "Number of steps not good")
