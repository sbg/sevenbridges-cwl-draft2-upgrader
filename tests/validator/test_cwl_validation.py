from unittest import TestCase
from unittest.mock import patch, MagicMock
import sevenbridges
from sbg_cwl_upgrader.validator.cwl_validation import CWLValidator
import warnings
import os
import yaml
from sbg_cwl_upgrader.validator.sbg_validate_js_cwl_v1 import main


class TestCWLValidatorLinting(TestCase):

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


class TestCWLValidatorCLI(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_file = os.path.join(os.path.dirname(__file__),
                                     'minimal-tool.cwl')

        with open(cls.test_file) as f:
            cls.tool = yaml.safe_load(f)

    @patch('logging.basicConfig', MagicMock())
    @patch('sbg_cwl_upgrader.validator.cwl_validation.CWLValidator',
           MagicMock())
    def test_local_validation_missing_file(self):
        """
        Check that missing file raises error.
        """
        with self.assertRaises(FileNotFoundError):
            main(['--input', '/foo/bar/foo.cwl'])

    @patch('logging.basicConfig', MagicMock())
    @patch('sbg_cwl_upgrader.validator.cwl_validation.CWLValidator.validate')
    def test_local_validation_conversion(self, mock_validator):
        """
        Check validator is called with the right value
        """
        main(['--input', self.test_file])
        mock_validator.assert_called_with(self.tool)

    @patch('logging.basicConfig', MagicMock())
    @patch('sevenbridges.Config', MagicMock())
    @patch('sevenbridges.Api')
    @patch('sbg_cwl_upgrader.validator.cwl_validation.CWLValidator.validate')
    def test_platform_validation(self, mock_validator, mock_api):
        """
        Check validator is called with the right value
        """
        mock_app = MagicMock(sevenbridges.App)
        mock_app.raw = self.tool
        mock_api_instance = mock_api.return_value
        mock_api_instance.apps.get.return_value = mock_app
        main(['--input', 'a/b/c'])

        mock_validator.assert_called_with(self.tool)


class TestCWLValidatorValidate(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_file = os.path.join(os.path.dirname(__file__),
                                     'minimal-tool.cwl')

        with open(cls.test_file) as f:
            cls.tool = yaml.safe_load(f)

        cls.wf = {
            "class": "Workflow",
            "cwlVersion": "v1.0",
            "inputs": [],
            "outputs": [],
            "steps": [
                {
                    "id": "1",
                    "run": cls.tool
                }
            ]
        }

    @patch(('sbg_cwl_upgrader.validator.'
            'cwl_validation.CWLValidator.validate_js_expressions_strict'))
    def test_simple_validate(self, mock_validation):
        CWLValidator().validate(self.tool)
        mock_validation.assert_called_once_with(self.tool)

    @patch(('sbg_cwl_upgrader.validator.'
            'cwl_validation.CWLValidator.validate_js_expressions_strict'))
    def test_recursive_validate(self, mock_validation):
        CWLValidator().validate(self.wf)
        mock_validation.assert_called_once_with(self.tool)

    def test_exception_missing_class(self):
        with self.assertRaises(IndexError):
            CWLValidator().validate({})

    def test_exception_wrong_class(self):
        with self.assertRaises(ValueError):
            CWLValidator().validate({"class": "FooTool"})

    def test_exception_missing_run(self):
        with self.assertRaises(IndexError):
            CWLValidator().validate(
                {"class": "Workflow", "steps": [{"id": 1}]}
            )
