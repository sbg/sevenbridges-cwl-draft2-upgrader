from unittest import TestCase
from unittest.mock import MagicMock, patch
from sbg_cwl_upgrader.converter.connection_checker import (
    ConnectionChecker, JS_ITEM_TO_LIST, JS_LIST_TO_ITEM
)


class TestConnectionChecker(TestCase):
    def setUp(self):
        self.connection_checker = ConnectionChecker()
        self.file_array_type = {
            "type": "array",
            "items": "File"
        }
        self.test_wf = {
            "class": "Workflow",
            "inputs": [
                {
                    "id": "in1",
                    "type": self.file_array_type
                },
                {
                    "id": "in2",
                    "type": "File"
                }
            ],
            "outputs": [
                {
                    "id": "out1",
                    "type": ["File"],
                    "outputSource": ["step1/out1"]
                },
                {
                    "id": "out2",
                    "type": [self.file_array_type],
                    "outputSource": ["step1/out2"]
                },
                {
                    "id": "out3",
                    "type": "File",
                    "outputSource": ["step2/out2"]
                }
            ],
            "steps": [
                {
                    "id": "step1",
                    "out": ["out1", "out2"],
                    "in": [
                        {
                            "id": "in1",
                            "source": "in1"
                        },
                        {
                            "id": "in2",
                            "source": "in2"
                        },
                        {
                            "id": "in3",
                            "source": "step2/out2"
                        }
                    ],
                    "run": {
                        "class": "MockTool",
                        "id": "tool1",
                        "inputs": [
                            {
                                "id": "in1",
                                "type": "File"
                            },
                            {
                                "id": "in2",
                                "type": self.file_array_type
                            },
                            {
                                "id": "in3",
                                "type": "File"
                            }
                        ],
                        "outputs": [
                            {
                                "id": "out1",
                                "type": self.file_array_type
                            },
                            {
                                "id": "out2",
                                "type": "File"
                            }
                        ]
                    }
                },
                {
                    "id": "step2",
                    "out": ["out1", "out2"],
                    "scatter": ["in1"],
                    "in": [
                        {
                            "id": "in1",
                            "source": "in1"
                        },
                        {
                            "id": "in2",
                            "source": "in2"
                        }
                    ],
                    "run": {
                        "class": "MockTool",
                        "id": "tool1",
                        "inputs": [
                            {
                                "id": "in1",
                                "type": "File"
                            },
                            {
                                "id": "in2",
                                "type": self.file_array_type
                            }
                        ],
                        "outputs": [
                            {
                                "id": "out1",
                                "type": self.file_array_type
                            },
                            {
                                "id": "out2",
                                "type": "File"
                            }
                        ]
                    }
                }
            ]
        }

    @patch('sys.stdout', MagicMock())
    def test_terminal_output_checker_file_to_list(self):
        wf = self.connection_checker.fix_terminal_output_types(self.test_wf)
        self.assertDictEqual(wf['outputs'][0]['type'], self.file_array_type)

    @patch('sys.stdout', MagicMock())
    def test_terminal_output_checker_list_to_file(self):
        wf = self.connection_checker.fix_terminal_output_types(self.test_wf)
        self.assertEqual(wf['outputs'][1]['type'], 'File')

    @patch('sys.stdout', MagicMock())
    def test_terminal_output_checker_scattered_file_to_file(self):
        wf = self.connection_checker.fix_terminal_output_types(self.test_wf)
        self.assertEqual(wf['outputs'][2]['type'], self.file_array_type)

    @patch('sys.stdout', MagicMock())
    def test_connection_checker_file_to_list(self):
        wf = self.connection_checker.fix_connection_matching(self.test_wf)
        self.assertEqual(wf['steps'][0]['in'][1]['valueFrom'],
                         JS_ITEM_TO_LIST)

    @patch('sys.stdout', MagicMock())
    def test_connection_checker_list_to_file(self):
        wf = self.connection_checker.fix_connection_matching(self.test_wf)
        self.assertEqual(wf['steps'][0]['in'][0]['valueFrom'],
                         JS_LIST_TO_ITEM)

    @patch('sys.stdout', MagicMock())
    def test_connection_checker_scattered_file_to_file(self):
        wf = self.connection_checker.fix_connection_matching(self.test_wf)
        self.assertEqual(wf['steps'][0]['in'][2]['valueFrom'],
                         JS_LIST_TO_ITEM)
