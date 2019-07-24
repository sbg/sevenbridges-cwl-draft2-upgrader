from unittest import TestCase
from unittest.mock import MagicMock
from sbg_cwl_upgrader.converter.workflow import CWLWorkflowConverter
from sbg_cwl_upgrader.converter.workflow import CWLToolConverter


class TestCWLWorkflowConverter(TestCase):

    def setUp(self):
        self.converter = CWLWorkflowConverter()

    def test_handle_source_string(self):
        d2_source = "#foo"
        self.assertEqual(self.converter.handle_source(d2_source),
                         ["foo"])

    def test_handle_source_list(self):
        d2_source = ["#foo", "#foo/bar"]
        self.assertEqual(self.converter.handle_source(d2_source),
                         ["foo", "foo/bar"])

    def test_handle_input(self):
        d2_input = {
            "id": "#foo",
            "required": False,
            "source": "#bar",
            "description": "This is great!"
        }
        v1_input = self.converter.handle_input(d2_input)
        self.assertNotIn("required",
                         v1_input)
        self.assertEqual(v1_input["source"], ["bar"])
        self.assertEqual(v1_input["id"], "foo")
        self.assertNotIn("description", v1_input)
        self.assertEqual(v1_input["doc"], d2_input["description"])

    def test_handle_output(self):
        d2_output = {
            "id": "#foo",
            "required": False,
            "source": "#bar",
            "description": "This is great!"
        }
        v1_output = self.converter.handle_output(d2_output)
        self.assertNotIn("required",
                         v1_output)
        self.assertEqual(v1_output["source"], ["bar"])
        self.assertEqual(v1_output["id"], "foo")
        self.assertNotIn("description", v1_output)
        self.assertEqual(v1_output["doc"], d2_output["description"])

    def test_handle_inputs(self):
        d2_inputs = [{
            "id": "#foo",
            "required": False,
            "source": "#bar",
            "description": "This is great!"
        }]
        self.converter.handle_input = MagicMock()
        self.converter.handle_inputs(d2_inputs)
        assert self.converter.handle_input.called

    def test_handle_outputs(self):
        d2_outputs = [{
            "id": "#foo",
            "required": False,
            "source": "#bar",
            "description": "This is great!"
        }]
        self.converter.handle_input = MagicMock()
        self.converter.handle_inputs(d2_outputs)
        assert self.converter.handle_input.called

    def test_handle_step(self):
        d2_step = {
            "id": "foo",
            "inputs": "foo",
            "outputs": "foo",
            "run": "foo",
            "scatter": "#foo"
        }
        self.converter.handle_inputs = MagicMock()
        self.converter.handle_outputs = MagicMock()
        self.converter.parse_step = MagicMock()
        self.converter.handle_id = MagicMock()
        v1_step = self.converter.handle_step(d2_step)
        self.converter.handle_inputs.assert_called()
        self.converter.handle_outputs.assert_called()
        self.converter.parse_step.assert_called()
        self.converter.handle_id.assert_called()
        self.assertNotIn("inputs", v1_step)
        self.assertNotIn("outputs", v1_step)

    def test_parse_step_wf(self):
        d2_step_wf = {
            "class": "Workflow"
        }
        CWLWorkflowConverter.convert_dict = MagicMock()
        self.converter.parse_step(d2_step_wf, "foo")
        CWLWorkflowConverter.convert_dict.assert_called()

    def test_parse_step_tool(self):
        d2_step_wf = {
            "class": "CommandLineTool"
        }
        CWLToolConverter.convert_dict = MagicMock()
        self.converter.parse_step(d2_step_wf, "foo")
        CWLToolConverter.convert_dict.assert_called()

    def test_parse_step_unknown(self):
        d2_step_wf = {
            "class": "FooBar"
        }
        with self.assertRaises(ValueError):
            self.converter.parse_step(d2_step_wf, "foo")

    def test_parse_step_wrong_type(self):
        d2_step_wf = {
            "class": ["FooBar"]
        }
        with self.assertRaises(ValueError):
            self.converter.parse_step(d2_step_wf, "foo")
