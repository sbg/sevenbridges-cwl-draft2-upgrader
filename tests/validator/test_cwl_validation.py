from unittest import TestCase
from sbg_cwl_upgrader.validator.cwl_validation import CWLValidator
import warnings


class TestCWLValidator(TestCase):

    def test_variable_not_defined(self):
        warnings.simplefilter('ignore')
        tool = {
                  "class": "CommandLineTool",
                  "cwlVersion": "v1.0",
                  "inputs": [
                    {
                      "id": "input",
                      "type": "File",
                      "inputBinding": {
                        "valueFrom": "${ a = 1; return a }"
                      }
                    }
                  ],
                  "requirements": [
                    {
                      "class": "InlineJavascriptRequirement"
                    }
                  ]
                }
        with self.assertLogs(logger='cwltool') as a_log:
            CWLValidator().validate_js_expressions_strict(tool)
        self.assertIn("'a' is not defined.", a_log.output[0])
        self.assertEqual(len(a_log.output), 2)

    def test_ES6_syntax(self):
        warnings.simplefilter('ignore')
        tool = {
            "class": "CommandLineTool",
            "cwlVersion": "v1.0",
            "inputs": [
                {
                    "id": "input",
                    "type": "File",
                    "inputBinding": {
                        "valueFrom": '${ return [0].map(v => v + 1) }'
                    }
                }
            ],
            "requirements": [
                {
                    "class": "InlineJavascriptRequirement"
                }
            ]
        }
        with self.assertLogs(logger='cwltool') as a_log:
            CWLValidator().validate_js_expressions_strict(tool)
        self.assertIn("ES6", a_log.output[0])
        self.assertEqual(len(a_log.output), 1)
