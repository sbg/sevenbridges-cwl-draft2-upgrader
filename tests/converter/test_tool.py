from unittest import TestCase
from unittest.mock import patch
import io
import sbg_cwl_upgrader
from sbg_cwl_upgrader.converter.cwl_converter import CWLConverterFacade
from sbg_cwl_upgrader.converter.tool import (Input, Output, Expression,
                                             CommandLineBinding,
                                             CWLToolConverter,
                                             OutputBinding, InputRecordField)
import random
import subprocess
import string
import os
import sys


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
        self.assertEqual(cwl1.cwl["type"], converted["type"])
        self.assertIn("valueFrom", cwl1.cwl["inputBinding"])
        # Check that default is not added by mistake
        self.assertNotIn("default", cwl1.cwl)

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
        self.assertEqual(cwl1.cwl["type"], converted["type"])
        self.assertIn("valueFrom", cwl1.cwl["inputBinding"])
        self.assertNotIn("default", cwl1.cwl)

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
        self.assertEqual(cwl1.cwl["type"], converted["type"])
        self.assertIn("valueFrom", cwl1.cwl["inputBinding"])

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

    def test_array_dict_with_no_separator(self):
        draft2 = {
            "type": {
                "type": "array",
                "items": "File"
            },
            "inputBinding": {
                "position": 0,
                "prefix": "-v",
                "separate": True,
            }
        }
        cwl1 = Input(draft2)
        self.assertIn("inputBinding", cwl1.cwl["type"])

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

    def test_record_type_position_added(self):
        draft2 = {
            "required": False,
            "type": [
                {
                    "type": "record",
                    "fields": [
                        {
                            "type": [
                                "File"
                            ],
                            "inputBinding": {
                                "position": 1,
                                "secondaryFiles": []
                            },
                            "name": "input_field"
                        },
                        {
                            "type": [
                                "null",
                                "string"
                            ],
                            "inputBinding": {
                                "position": 1
                            },
                            "name": "input_field_1"
                        }
                    ],
                    "name": "input"
                }
            ]
        }
        cwl1 = Input(draft2)
        self.assertEqual(cwl1.cwl['type']['type'], 'record')
        self.assertEqual(cwl1.cwl['inputBinding']['position'], 1)
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

    def test_enum_name_changed(self):
        draft2 = {
            "id": "#foo",
            "type": [
                "null",
                {
                    "type": "enum",
                    "symbols": ["a", "b"],
                    "name": "null"
                }
            ]
        }
        cwl1 = Input(draft2, in_id='foo')
        self.assertEqual(cwl1.cwl['type'][1]["name"], 'foo')


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

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_glob_with_braces(self, mock_stdout):
        """
        glob with brace expand should be split into indiviudal components
        and run corectly on cwltool.
        :return:
        """

        v1_file = os.path.join(
            os.path.dirname(__file__),
            'mini_tool_cwl1_{}.json'.format(
                ''.join(random.sample(string.ascii_lowercase, 3))
            )
        )
        d2_file = os.path.join(os.path.dirname(__file__),
                               'tool_glob_with_braces_d2.cwl')
        CWLConverterFacade(d2_file,
                           output=v1_file)

        process = subprocess.Popen(
            [sys.executable, "-m", "cwltool", v1_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, _ = process.communicate()
        os.remove(v1_file)

        self.assertEqual(process.returncode, 0)
        passed = ("BatchText" in str(stdout)) or ("TextBatch" in str(stdout))
        self.assertTrue(passed)
        self.assertIn("Converting done.", mock_stdout.getvalue())

    def test_glob_expression(self):
        draft2 = {
            "glob": {
                "script": "{ return '*.txt' }"
            }
        }
        cwl1 = OutputBinding(draft2)
        self.assertIn("return '*.txt'", cwl1.cwl['glob'])

    def test_outputEval_expression(self):
        draft2 = {
            "outputEval": {
                "script": "{ return '*.txt' }"
            }
        }
        cwl1 = OutputBinding(draft2)
        self.assertIn("return '*.txt'", cwl1.cwl['outputEval'])

    def test_metadata_inherit(self):
        draft2 = {
            "sbg:inheritMetadataFrom": "#input"
        }
        cwl1 = OutputBinding(draft2)
        self.assertIn("outputEval", cwl1.cwl)
        self.assertIn("inheritMetadata(self, inputs.input)",
                      cwl1.cwl["outputEval"])

    def test_metadata_setting_with_inherit(self):
        draft2 = {
            "sbg:metadata": {
                "foo": "12",
                "bar": {
                    "class": "Expression",
                    "engine": "#cwl-js-engine",
                    "script": "{\n    return $job.inputs.input.path\n}"
                }
            },
            "sbg:inheritMetadataFrom": "#input"
        }
        cwl1 = OutputBinding(draft2)
        self.assertIn("outputEval", cwl1.cwl)
        self.assertIn("foo", cwl1.cwl["outputEval"])
        self.assertIn("bar", cwl1.cwl["outputEval"])
        self.assertIn("inheritMetadata", cwl1.cwl["outputEval"])
        self.assertIn("return inputs.input.path", cwl1.cwl["outputEval"])
        # Check inheriting is before adding custom keys
        self.assertGreater(cwl1.cwl['outputEval'].find("foo"),
                           cwl1.cwl['outputEval'].find("inheritMetadata"))

    def test_metadata_setting_with_outputEval(self):
        """
        Test that combination of outputEval and metadata inheriting is all
        well merged in a single outputEval in CWL1.0
        :return:
        """
        draft2 = {
            "sbg:metadata": {
                "foo": "12",
                "bar": {
                    "class": "Expression",
                    "engine": "#cwl-js-engine",
                    "script": "{\n    return $job.inputs.input.path\n}"
                }
            },
            "sbg:inheritMetadataFrom": "#input",
            "outputEval": {
                    "class": "Expression",
                    "engine": "#cwl-js-engine",
                    "script": "{\n    return $self[0]\n}"
                }
        }
        cwl1 = OutputBinding(draft2)
        self.assertIn("outputEval", cwl1.cwl)
        self.assertIn("foo", cwl1.cwl["outputEval"])
        self.assertIn("bar", cwl1.cwl["outputEval"])
        self.assertIn("inheritMetadata", cwl1.cwl["outputEval"])
        self.assertIn("return inputs.input.path", cwl1.cwl["outputEval"])
        # Check inheriting is before adding custom keys
        self.assertGreater(cwl1.cwl['outputEval'].find("foo"),
                           cwl1.cwl['outputEval'].find("inherit"))
        # Check original outputEval is preserved and added after inherit
        self.assertGreater(cwl1.cwl['outputEval'].find("self[0]"),
                           cwl1.cwl['outputEval'].find("inherit"))

    def test_keys_removed(self):
        """
        Test id and secondaryFiles keys are removed
        :return:
        """
        draft2 = {
            "id": "#foo",
            "secondaryFiles": ["bar"]
        }
        cwl1 = OutputBinding(draft2)
        self.assertNotIn("id", cwl1.cwl)
        self.assertNotIn("secondaryFiles", cwl1.cwl)


class TestInputRecordField(TestCase):
    @patch.object(Input, "__init__", lambda x, y: None)
    @patch.object(sbg_cwl_upgrader.converter.tool.Input, 'to_dict')
    def test_input_to_dict_called(self, mock_to_dict):
        draft2 = True
        InputRecordField(draft2)
        mock_to_dict.assert_called_once()


class TestExpression(TestCase):
    def test_parse_js_called(self):
        draft2 = {
            "script": "{ return 1}"
        }
        self.assertIn("return", Expression(draft2).to_dict())


class TestCommandLineBinding(TestCase):
    def setUp(self):
        self.d2 = {
            "valueFrom": {
                "script": "{ return 1 }"
            },
            "id": "#foo",
            "secondaryFiles": []
        }

    def test_keys_added_deleted(self):
        """
        Keys "id" and "secondaryFiles" should be removed.
        Key "shellQuote" should be False.
        :return:
        """
        v1 = CommandLineBinding(self.d2).to_dict()
        self.assertNotIn("secondaryFiles", v1)
        self.assertNotIn("id", v1)
        self.assertFalse(v1["shellQuote"])

    def test_valueFrom_expression_called(self):
        self.assertIn("return",
                      CommandLineBinding(self.d2).to_dict()['valueFrom'])


class TestCWLToolConverter(TestCase):
    def setUp(self):
        self.tool_converter = CWLToolConverter()

    def test_is_staged_file_true(self):
        draft2 = {
            "type": ["null", "File"],
            "sbg:stageInput": "copy"
        }
        self.assertTrue(self.tool_converter._is_staged_file(draft2))

    def test_is_staged_file_false(self):
        draft2 = {
            "type": ["null", "File"]
        }
        self.assertFalse(self.tool_converter._is_staged_file(draft2))

    def test_is_staged_file_array_true(self):
        draft2 = {
            "type": ["null", {"type": "array", "items": "File"}],
            "sbg:stageInput": "copy"
        }
        self.assertTrue(self.tool_converter._is_staged_array_of_files(draft2))

    def test_is_staged_file_array_false(self):
        draft2 = {
            "type": ["null", {"type": "array", "items": "File"}]
        }
        self.assertFalse(self.tool_converter._is_staged_array_of_files(draft2))

    def test_proper_files_staged(self):
        draft2 = [
            {
                "id": "#foo",
                "sbg:stageInput": "copy"
            },
            {
                "id": "bar"
            }
        ]
        cwl1 = self.tool_converter._stage_inputs(draft2)
        self.assertEqual("$(inputs.foo)", cwl1[0]["entry"])
        self.assertTrue(cwl1[0]["writable"])
        self.assertNotIn("$(inputs.bar)", cwl1)

    def test_input_position_shift_with_offset(self):
        draft2 = [
            {
                "id": "foo",
                "inputBinding": {
                    "position": 5
                }
            },
            {
                "id": "bar",
                "inputBinding": {
                    "position": -3
                }
            },
            {
                "id": "baz",
                "inputBinding": {
                    "prefix": "-a"
                }
            },
            {
                "id": "baq"
            }
        ]

        cwl1 = self.tool_converter._handle_inputs(draft2,
                                                  list(range(100)),
                                                  30,
                                                  -3)
        # should be 5 + 100 - 30 - (-3) = 78
        self.assertEqual(cwl1['foo']['inputBinding']['position'], 78)
        # should be -3 + 100 - 30 - (-3) = 70
        self.assertEqual(cwl1['bar']['inputBinding']['position'], 70)
        # should be 0 + 100 - 30 - (-3) = 73
        self.assertEqual(cwl1['baz']['inputBinding']['position'], 73)
        # baq should not get inputBinding
        self.assertNotIn('inputBinding', cwl1['baq'])

    def test_inputs_deleted_keys(self):
        draft2 = [{"id": "#foo", "sbg:stageInput": "copy", "doc": "foo"}]
        cwl1 = self.tool_converter._handle_inputs(draft2, [])
        self.assertIsInstance(cwl1, dict)
        self.assertNotIn("sbg:stageInput", cwl1["foo"])
        self.assertNotIn("id", cwl1["foo"])
        self.assertIn("doc", cwl1["foo"])

    def test_handle_outputs(self):
        draft2 = [
            {
                "id": "#foo",
                "outputBinding": {
                    "glob": "*"
                }
            }
        ]
        cwl1 = self.tool_converter._handle_outputs(draft2)
        self.assertIsInstance(cwl1, dict)
        self.assertNotIn("id", cwl1["foo"])
        self.assertIn("outputBinding", cwl1["foo"])

    def test_handle_hints(self):
        """
        Ensure docker and resource requirements are moved to requirements
        :return:
        """
        draft2 = [
            {
                "class": "sbg:CPURequirement",
                "value": 1
            },
            {
                "class": "sbg:MemRequirement",
                "value": 1
            },
            {
                "class": "DockerRequirement",
                "dockerPull": "ubuntu"
            },
            {
                "class": "sbg:AWSInstanceType",
                "value": "c4.2xlarge"
            }
        ]
        cwl1 = self.tool_converter._handle_hints(draft2)
        self. assertIsInstance(cwl1, list)
        self.assertListEqual(cwl1, [
            {
                "class": "sbg:AWSInstanceType",
                "value": "c4.2xlarge"
            }
        ])

    def test_handle_requirements_hints_moved(self):
        """
        Test docker and resources are moved from hints to requirements.
        Also check if existing requirements are preserved
        :return:
        """
        draft2_hints = [
            {
                "class": "sbg:CPURequirement",
                "value": {
                    "class": "Expression",
                    "script": "{ return 1 }"
                }
            },
            {
                "class": "sbg:MemRequirement",
                "value": 1
            },
            {
                "class": "DockerRequirement",
                "dockerPull": "ubuntu"
            },
            {
                "class": "SomeHint"
            }
        ]
        cwl1 = self.tool_converter._handle_requirements(
            draft2_hints,
            [{"class": "EnvVarRequirement"}],
            []
        )
        expected_requirements = [
            "DockerRequirement",
            "ResourceRequirement",
            "ShellCommandRequirement",
            "InlineJavascriptRequirement",
            "EnvVarRequirement",
            "InitialWorkDirRequirement"
        ]
        self.assertIsInstance(cwl1, list)
        self.assertListEqual(sorted(expected_requirements),
                             sorted([req["class"] for req in cwl1]))

    def test_dockerImageId_removed(self):
        """
        Test if dockerImageId is removed upon conversion
        :return:
        """
        draft2_hints = [
            {
                "class": "DockerRequirement",
                "dockerPull": "ubuntu",
                "dockerImageId": "foo"
            }
        ]
        cwl1_expected = [
            {
                "class": "DockerRequirement",
                "dockerPull": "ubuntu"
            }
        ]
        cwl1 = self.tool_converter._handle_requirements(
            draft2_hints,
            [],
            []
        )
        for req in cwl1:
            if req.get('class') == 'DockerRequirement':
                cwl1_req = req

        self.assertDictEqual(cwl1_req, cwl1_expected[0])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_create_file_requirement(self, mock_stdout):
        """
        Test that file literals and expressions are saved to Initial Work Dir
        Requirement. Also check if warning is printed out if "/" is in file
        name.
        :return:
        """
        draft2 = [
            {
                "class": "CreateFileRequirement",
                "fileDef": [
                    {
                        "filename": "foo/bar",
                        "fileContent": "$(baz)"
                    },
                    {
                        "filename": {
                            "class": "Expression",
                            "script": "{ return 'foo/bar' }"
                        },
                        "fileContent": {
                            "class": "Expression",
                            "script": "{ return '$(baz)')"
                        }
                    }
                ]
            }
        ]

        cwl1 = self.tool_converter._handle_requirements([], draft2, [])
        expected = {
            'class': 'InitialWorkDirRequirement',
            'listing': [
                {
                    'entryname': 'foo/bar',
                    'entry': '$("$")(baz)'
                },
                {
                    'entryname': "${\n    return 'foo/bar'\n}",
                    'entry': "${\n    {\n        return '$(baz)')\n}"
                }
            ]
        }

        iwd_req = [req for req in cwl1
                   if req["class"] == "InitialWorkDirRequirement"][0]

        self.assertDictEqual(expected, iwd_req)
        self.assertIn("Please modify name", mock_stdout.getvalue())

    def test_handle_base_command(self):
        """
        Test only non expressions from base command are added to cwl1.
        Offset is number of items before first expression.
        :return:
        """
        draft2 = [
            "one",
            {
                "class": "Expression",
                "script": "two"
            },
            "three"
        ]
        offset, out = self.tool_converter._handle_base_command(draft2)
        self.assertEqual(offset, 1)
        self.assertEqual(out, ["one"])

    def test_handle_arguments(self):
        """
        Test base command items are added to arguments
        :return:
        """
        args = [
            "four",
            {
                "class": "Expression",
                "script": "{ return 'five'}"
            }
        ]
        basecommand = [
            "one",
            {
                "class": "Expression",
                "script": "two"
            },
            "three"
        ]
        cwl1 = self.tool_converter._handle_arguments(args, basecommand,
                                                     offset=1)
        self.assertEqual(len(cwl1), 4)

    def test_cleanup_inherit_metadata(self):
        """
        Remove inheriting metadata from non-existing input
        :return:
        """
        inputs = [
            {
                "id": "#foo"
            }
        ]
        outputs = [
            {
                "id": "#outfoo",
                "outputBinding":
                    {
                        "sbg:inheritMetadataFrom": "#foo"
                    }
            },
            {
                "id": "#outbar",                "outputBinding":
                    {
                        "sbg:inheritMetadataFrom": "#bar"
                    }
            }
        ]
        out = self.tool_converter._cleanup_invalid_inherit_metadata(
            inputs, outputs
        )
        self.assertIn("sbg:inheritMetadataFrom", out[0]["outputBinding"])
        self.assertNotIn("sbg:inheritMetadataFrom", out[1]["outputBinding"])

    def test_get_lowest_input_position(self):
        inputs = [
            {
                "id": "#foo",
                "inputBinding":
                    {
                        "position": 1
                    }
            },
            {
                "id": "#bar",
                "inputBinding":
                    {
                        "position": 4
                    }
            },
            {
                "id": "#buzz",
                "inputBinding":
                    {
                        "position": -5
                    }
            }
        ]
        self.assertEqual(
            -5,
            self.tool_converter._get_lowest_negative_input_position(inputs)
        )
        self.assertEqual(
            0,
            self.tool_converter._get_lowest_negative_input_position(inputs[:1])
        )
