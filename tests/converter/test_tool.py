from unittest import TestCase
from sbg_cwl_upgrader.converter.tool import Input, Output, OutputBinding


class TestInput(TestCase):

    def test_doc(self):
        draft2 = {
            "description": "Some description."
        }
        cwl1 = Input(draft2)
        self.assertEqual(cwl1.cwl['doc'], draft2['description'])
        self.assertNotIn('description', cwl1.cwl)

    def test_secondary_files(self):
        draft2 = {
            "inputBinding": {
                "secondaryFiles": [
                    ".bai", ".fai", ".crai"
                ]
            }
        }
        cwl1 = Input(draft2)
        self.assertEqual(cwl1.cwl['secondaryFiles'],
                         draft2["inputBinding"]["secondaryFiles"])

    def test_secondary_files_typecheck(self):
        draft2 = {
            "inputBinding": {
                "secondaryFiles": [
                    7
                ]
            }
        }
        with self.assertRaises(Exception):
            Input(draft2)

    def test_item_separator_true_separate(self):
        draft2 = {
            "type": [{
                "type": "array",
                "items": "string"
            }],
            "inputBinding": {
                "prefix": "-a",
                "itemSeparator": None,
                "separate": True,
                "position": 1
            }
        }
        converted = {
            "type": [{
                "type": "array",
                "items": "string",
                "inputBinding": {
                    "prefix": "-a",
                    "separate": True
                }
            }],
            "inputBinding": {
                "position": 1,
                "shellQuote": False
            }
        }
        cwl1 = Input(draft2)
        self.assertEqual(cwl1.cwl, converted)

    def test_item_separator_false_separate_optional(self):
        draft2 = {
            "type": [
                "null", {
                    "type": "array",
                    "items": "string"
                }],
            "inputBinding": {
                "prefix": "-a",
                "itemSeparator": None,
                "separate": False
            }
        }
        converted = {
            "type": [
                "null", {
                    "type": "array",
                    "items": "string",
                    "inputBinding": {
                        "prefix": "-a",
                        "separate": False
                    }
                }]
        }
        cwl1 = Input(draft2)
        self.assertEqual(cwl1.cwl, converted)

    def test_item_separator_without_separate(self):
        draft2 = {
            "type": [{
                "type": "array",
                "items": "string"
            }],
            "inputBinding": {
                "prefix": "-a",
                "itemSeparator": None
            }
        }
        converted = {
            "type": [{
                "type": "array",
                "items": "string",
                "inputBinding": {
                    "prefix": "-a"
                }
            }]
        }

        cwl1 = Input(draft2)
        self.assertEqual(cwl1.cwl, converted)

    def test_item_separator_without_prefix(self):
        draft2 = {
            "type": [{
                "type": "array",
                "items": "string"
            }],
            "inputBinding": {
                "itemSeparator": 'a'
            }
        }
        cwl1 = Input(draft2)
        self.assertNotIn("itemSeparator", cwl1.cwl["inputBinding"])

    def test_array_with_no_separator(self):
        draft2 = {
            "type": [
                {
                    "type": "array",
                    "items": "File"
                }
            ],
            "inputBinding": {
                "position": 0,
                "prefix": "-v",
                "separate": True,
            }
        }
        cwl1 = Input(draft2)
        self.assertIn("inputBinding", cwl1.cwl["type"][0])

    def test_optional_type(self):
        draft2 = {
            "required": False,
            "type": [
              "File", "null"
            ]
        }
        cwl1 = Input(draft2)
        self.assertEqual(cwl1.cwl['type'], 'File?')
        self.assertNotIn('required', cwl1.cwl)

    def test_valueFrom_adding_default_0(self):
        draft2 = {
            "type": [
              "string", "null"
            ],
            "inputBinding": {
                "valueFrom": "{return a}"
            }
        }
        cwl1 = Input(draft2, in_id="input")
        self.assertEqual(cwl1.cwl['default'], 0)
        self.assertIn('self = null', cwl1.cwl["inputBinding"]['valueFrom'])
        self.assertIn('inputs.input = null',
                      cwl1.cwl["inputBinding"]['valueFrom'])

    def test_delete_cmd_include(self):
        draft2 = {
            "inputBinding": {
                "sbg:cmdInclude": True
            }
        }
        cwl1 = Input(draft2, in_id="input")
        self.assertNotIn('sbg:cmdInclude', cwl1.cwl["inputBinding"])


class TestOutput(TestCase):
    def test_doc(self):
        draft2 = {
            "description": "Some description."
        }
        cwl1 = Output(draft2)
        self.assertEqual(cwl1.cwl['doc'], draft2['description'])
        self.assertNotIn('description', cwl1.cwl)

    def test_secondary_files(self):
        draft2 = {
            "outputBinding": {
                "secondaryFiles": [
                    ".bai", ".fai", ".crai"
                ]
            }
        }
        cwl1 = Output(draft2)
        self.assertEqual(cwl1.cwl["secondaryFiles"],
                         draft2["outputBinding"]["secondaryFiles"])

    def test_optional_type(self):
        draft2 = {
            "required": False,
            "type": [
              "File", "null"
            ]
        }
        cwl1 = Output(draft2)
        self.assertEqual(cwl1.cwl['type'], 'File?')
        self.assertNotIn('required', cwl1.cwl)


class TestOutputBinding(TestCase):
    def test_glob_subdirectory(self):
        draft2 = {
            "glob": "./a/b/c"
        }
        cwl1 = OutputBinding(draft2)
        self.assertEqual(cwl1.cwl['glob'], 'a/b/c')
