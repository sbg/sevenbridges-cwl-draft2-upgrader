from unittest import TestCase
from unittest.mock import patch
import os
import shutil
import io
from sbg_cwl_upgrader.decomposer.local import (safe_dump_yaml,
                                               breakdown_wf_local)
from sbg_cwl_upgrader.cwl_utils import as_list


def safe_remove(file_paths):
    for file_path in as_list(file_paths):
        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


class TestSafeDumpYaml(TestCase):
    def test_regular_save(self):
        safe_remove("foo.cwl")
        safe_dump_yaml('foo.cwl', {"foo": "bar"})
        assert os.path.isfile("foo.cwl")
        safe_remove("foo.cwl")

    def test_safe_dumping(self):
        """
        Test that dumping over existing file will not override it, but add
        _n_ prefix to the file name
        :return:
        """
        safe_remove(["foo.cwl", "_1_foo.cwl"])
        safe_dump_yaml('foo.cwl', {"foo": "bar"})
        safe_dump_yaml('foo.cwl', {"foo": "bar"})
        assert os.path.isfile("foo.cwl")
        assert os.path.isfile("_1_foo.cwl")
        safe_remove(["foo.cwl", "_1_foo.cwl"])

    def test_safe_dumping_directory(self):
        """
        Test that dumping over existing file will not override it, but add
        _n_ prefix to the file name
        :return:
        """
        safe_remove(["bar"])
        safe_dump_yaml('bar/foo.cwl', {"foo": "bar"})
        safe_dump_yaml('bar/foo.cwl', {"foo": "bar"})
        assert os.path.isfile("bar/foo.cwl")
        assert os.path.isfile("bar/_1_foo.cwl")
        safe_remove(["bar"])


class TestBreakdownWFLocal(TestCase):
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_simple_workflow(self, mock_stdout):
        """
        Test that a simple workflow is decomposed and packed in steps dir.
        Also test if decomposing start/stop message is printed out.
        """
        test_wf = {
            "class": "Workflow",
            "steps": [
                {
                    "id": "1",
                    "run": {
                        "class": "CommandLineTool",
                        "id": "this is tool 1"
                    }
                },
                {
                    "id": "2",
                    "run": {
                        "class": "CommandLineTool",
                        "id": "this is tool 2"
                    }
                }
            ]
        }

        os.mkdir('test_simple')

        breakdown, _ = breakdown_wf_local("test_simple/foo.cwl",
                                          nested_wf_json=test_wf)
        self.assertEqual(os.path.basename(breakdown), "foo_decomposed.cwl")
        assert os.path.isdir("test_simple/steps")
        assert os.path.isfile("test_simple/steps/1.cwl")
        assert os.path.isfile("test_simple/steps/2.cwl")
        self.assertIn("Decomposing workflow", mock_stdout.getvalue())
        self.assertIn("Rewiring done.", mock_stdout.getvalue())
        safe_remove(["test_simple/"])

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_duplicate_nested_workflow(self, mock_stdout):
        """
        Test that a duplicate nested workflow is reused.
        """
        basedir = os.path.dirname(__file__)
        steps_dir = os.path.join(basedir, "steps")
        test_wf = os.path.join(basedir,
                               'duplicate_nested_wf.json')
        safe_remove(steps_dir)
        breakdown, _ = breakdown_wf_local(test_wf)
        self.assertEqual(os.path.basename(breakdown),
                         "duplicate_nested_wf_decomposed.cwl")
        # Check if duplicates are not created
        assert os.path.isdir(steps_dir)
        assert os.path.isfile(os.path.join(steps_dir, "1.cwl"))
        assert not os.path.isfile(os.path.join(steps_dir, "_1_1.cwl"))
        assert os.path.isfile(os.path.join(steps_dir, "2.cwl"))
        assert not os.path.isfile(os.path.join(steps_dir, "_1_2.cwl"))
        assert os.path.isfile(os.path.join(steps_dir, "wf1.cwl"))
        assert not os.path.isfile(os.path.join(steps_dir, "wf2.cwl"))
        self.assertIn("Decomposing workflow", mock_stdout.getvalue())
        self.assertIn("Rewiring done.", mock_stdout.getvalue())
        safe_remove([steps_dir,
                     os.path.join(basedir,
                                  'duplicate_nested_wf_decomposed.cwl')
                     ])
