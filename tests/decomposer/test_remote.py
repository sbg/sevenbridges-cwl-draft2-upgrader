from unittest import TestCase
from unittest.mock import patch, MagicMock, call
import io
import os
import json
import sevenbridges
from sbg_cwl_upgrader.decomposer.remote import breakdown_wf_sbg


class TestBreakdownWFRemote(TestCase):

    @patch('sevenbridges.Api')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_simple_workflow(self, mock_stdout, mock_api):
        """
        Test that a simple workflow is decomposed and packed in steps dir.
        Also test if decomposing start/stop message is printed out.
        """
        test_wf = {
            "class": "Workflow",
            "cwlVersion": "v1.0",
            "label": "test_wf",
            "sbg:id": "a/b/test_wf",
            "id": "test_wf",
            "steps": [
                {
                    "id": "1",
                    "run": {
                        "class": "CommandLineTool",
                        "cwlVersion": "v1.0",
                        "id": "1",
                        "sbg:id": "a/b/1"
                    }
                },
                {
                    "id": "2",
                    "run": {
                        "class": "CommandLineTool",
                        "cwlVersion": "v1.0",
                        "id": "2",
                        "sbg:id": "a/b/2"
                    }
                }
            ]
        }
        mock_app_1 = MagicMock(sevenbridges.App)
        mock_app_1.raw = test_wf["steps"][0]["run"]
        mock_app_2 = MagicMock(sevenbridges.App)
        mock_app_2.raw = test_wf["steps"][1]["run"]
        mock_app_wf = MagicMock(sevenbridges.App)
        mock_app_wf.raw = test_wf

        apps_dict = {
            "a/b/1": mock_app_1,
            "a/b/2": mock_app_2,
            "a/b/test-wf": mock_app_wf
        }

        mock_api.apps.get.side_effect = apps_dict.get

        breakdown, installed_apps = breakdown_wf_sbg(wf_name="test_wf",
                                                     project_id="a/b",
                                                     wf_json=test_wf,
                                                     api=mock_api)

        self.assertIsInstance(breakdown.raw, dict)
        mock_api.apps.get.assert_has_calls([call('a/b/1'),
                                            call('a/b/2'),
                                            call('a/b/test-wf')])

        self.assertIn("Decomposing workflow", mock_stdout.getvalue())
        self.assertIn("Rewiring done.", mock_stdout.getvalue())

    @patch('sevenbridges.Api')
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_duplicate_nested_workflow(self, mock_stdout, mock_api):
        """
        Test that a duplicate nested workflow is reused.
        """
        basedir = os.path.dirname(__file__)
        test_wf = os.path.join(basedir,
                               'duplicate_nested_wf.json')
        with open(test_wf, 'r') as f:
            wf_json = json.load(f)

        mock_app_1 = MagicMock(sevenbridges.App)
        mock_app_1.raw = wf_json["steps"][0]["run"]["steps"][0]["run"]
        mock_app_2 = MagicMock(sevenbridges.App)
        mock_app_2.raw = wf_json["steps"][0]["run"]["steps"][1]["run"]

        mock_app_wf1 = MagicMock(sevenbridges.App)
        mock_app_wf1.raw = wf_json["steps"][0]["run"]
        mock_app_wf2 = MagicMock(sevenbridges.App)
        mock_app_wf2.raw = wf_json

        apps_dict = {
            "a/b/1": mock_app_1,
            "a/b/2": mock_app_2,
            "a/b/wf1": mock_app_wf1,
            "a/b/wf2": mock_app_wf2
        }
        mock_api.apps.get.side_effect = apps_dict.get

        breakdown, installed_apps = breakdown_wf_sbg('wf2',
                                                     'a/b',
                                                     wf_json,
                                                     mock_api)

        self.assertIsInstance(breakdown.raw, dict)
        # Check duplicates are called once
        mock_api.apps.get.assert_has_calls([call('a/b/1'),
                                            call('a/b/2'),
                                            call('a/b/wf1'),
                                            call('a/b/wf2')])

        self.assertIn("Decomposing workflow", mock_stdout.getvalue())
        self.assertIn("Rewiring done.", mock_stdout.getvalue())
