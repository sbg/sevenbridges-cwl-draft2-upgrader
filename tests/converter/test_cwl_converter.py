from sbg_cwl_upgrader.converter.cwl_converter import CWLConverterFacade
import json
import sevenbridges
from sevenbridges import NotFound
from unittest import TestCase
from unittest.mock import patch, MagicMock, ANY
import os
import io
import subprocess
import sys
import random
import string


def mock_app_get_not_found(_, api=None):
    raise NotFound("")


class TestCWLConverter(TestCase):
    @patch('sys.stderr', MagicMock())
    @patch('sys.stdout', MagicMock())
    def test_all_steps(self):
        """
        Test a full conversion for a complex draft2 workflow.
        :return:
        """
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

    @patch('sys.stdout', MagicMock())
    @patch('sys.stderr', MagicMock())
    @patch('sbg_cwl_upgrader.converter.cwl_converter.prompt_for_confirmation',
           MagicMock(return_value=False)
           )
    def test_mini_wf(self):
        """
        Test that a mini workflow is executable with cwltool after converting.
        Workflow receives string input "foo" and outputs "foo foo\n".
        :return:
        """
        v1_file = os.path.join(
            os.path.dirname(__file__),
            'mini_wf_cwl1_{}.cwl'.format(
                ''.join(random.sample(string.ascii_lowercase, 3))
            )
        )
        d2_file = os.path.join(os.path.dirname(__file__),
                               'mini_wf_d2.cwl')
        CWLConverterFacade(d2_file, output=v1_file)

        process = subprocess.Popen(
            [sys.executable, "-m", "cwltool", v1_file, "--input", "foo"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, _ = process.communicate()
        os.remove(v1_file)

        self.assertEqual(process.returncode, 0)
        self.assertIn("foo foo", str(stdout))

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_mini_tool(self, mock_stdout):
        """
        Test that a mini tool is executable with cwltool after converting.
        Workflow receives integer input 1 and outputs "1 1 1\n".
        :return:
        """

        v1_file = os.path.join(
            os.path.dirname(__file__),
            'mini_tool_cwl1_{}.json'.format(
                ''.join(random.sample(string.ascii_lowercase, 3))
            )
        )
        d2_file = os.path.join(os.path.dirname(__file__),
                               'mini_tool_d2.cwl')
        CWLConverterFacade(d2_file,
                           output=v1_file)

        process = subprocess.Popen(
            [sys.executable, "-m", "cwltool", v1_file, "--in", "1"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, _ = process.communicate()
        os.remove(v1_file)

        self.assertEqual(process.returncode, 0)
        self.assertIn("1 1 1", str(stdout))
        self.assertIn("Converting done.", mock_stdout.getvalue())

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_base_command_with_spaces(self, mock_stdout):
        """
        baseCommand with spaces should be split into indiviudal components
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
                               'tool_base_command_with_spaces_d2.cwl')
        CWLConverterFacade(d2_file,
                           output=v1_file)

        process = subprocess.Popen(
            [sys.executable, "-m", "cwltool", v1_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, _ = process.communicate()
        os.remove(v1_file)

        self.assertEqual(process.returncode, 0)
        self.assertIn("A test string", str(stdout))
        self.assertIn("Converting done.", mock_stdout.getvalue())

    @patch('sys.stdout', MagicMock())
    def test_local_input_no_output(self):
        """
        Check exception is raised for local input and no output
        """
        with self.assertRaises(Exception):
            CWLConverterFacade('wf.cwl')

    @patch(
        'sbg_cwl_upgrader.converter.cwl_converter.CWLConverterFacade._parse'
    )
    @patch('sevenbridges.Api')
    @patch('sevenbridges.Config', MagicMock())
    @patch('sys.stdout', MagicMock())
    @patch('sbg_cwl_upgrader.converter.cwl_converter.prompt_for_confirmation',
           MagicMock(return_value=False))
    def test_platform_input_no_output_update_true(self, mock_api, mock_parse):
        """
        Check if update true submits create_revision
        """

        mock_app_wf1 = MagicMock(sevenbridges.App)
        mock_app_wf1.raw = {
            "id": "a/b/c",
            "class": "CommandLineTool",
            "cwlVersion": "sbg:draft-2"
        }
        mock_api_instance = mock_api.return_value
        mock_api_instance.apps.get.return_value = mock_app_wf1
        mock_parse.return_value = mock_app_wf1.raw
        CWLConverterFacade("a/b/c", validate=False,
                           decompose=False, update=True)

        mock_parse.assert_called()
        mock_api_instance.apps.create_revision.assert_called_once_with(
            'a/b/c', ANY, ANY, api=mock_api_instance
        )
        mock_api_instance.apps.get.assert_called_with('a/b/c',
                                                      api=mock_api_instance)

    @patch(
        'sbg_cwl_upgrader.converter.cwl_converter.CWLConverterFacade._parse'
    )
    @patch('sevenbridges.Api')
    @patch('sevenbridges.Config', MagicMock())
    @patch('sys.stdout', MagicMock())
    @patch('sbg_cwl_upgrader.converter.cwl_converter.prompt_for_confirmation',
           MagicMock(return_value=True))
    def test_platform_input_no_output_update_true_prompt(
            self, mock_api, mock_parse
    ):
        """
        Check if update true via prompt submits create_revision
        """

        mock_app_wf1 = MagicMock(sevenbridges.App)
        mock_app_wf1.raw = {
            "id": "a/b/c",
            "class": "CommandLineTool",
            "cwlVersion": "sbg:draft-2"
        }
        mock_api_instance = mock_api.return_value
        mock_api_instance.apps.get.return_value = mock_app_wf1
        mock_parse.return_value = mock_app_wf1.raw
        CWLConverterFacade("a/b/c", validate=False,
                           decompose=False, update=False)

        mock_parse.assert_called()
        mock_api_instance.apps.create_revision.assert_called_once_with(
            'a/b/c', ANY, ANY, api=mock_api_instance
        )
        mock_api_instance.apps.get.assert_called_with('a/b/c',
                                                      api=mock_api_instance)

    @patch(
        'sbg_cwl_upgrader.converter.cwl_converter.CWLConverterFacade._parse'
    )
    @patch('sevenbridges.Api')
    @patch('sevenbridges.Config', MagicMock())
    @patch('sys.stdout', MagicMock())
    @patch('sbg_cwl_upgrader.converter.cwl_converter.prompt_for_confirmation',
           MagicMock(return_value=False))
    def test_platform_input_no_output_update_false(
            self, mock_api, mock_parse
    ):
        """
        Check if update true via prompt submits create_revision
        """

        mock_app_wf1 = MagicMock(sevenbridges.App)
        mock_app_wf1.raw = {
            "id": "a/b/c",
            "class": "CommandLineTool",
            "cwlVersion": "sbg:draft-2"
        }
        mock_api_instance = mock_api.return_value
        mock_api_instance.apps.get.return_value = mock_app_wf1
        mock_parse.return_value = mock_app_wf1.raw
        CWLConverterFacade("a/b/c", validate=False,
                           decompose=False, update=False)

        mock_parse.assert_called()
        mock_api_instance.apps.create_revision.assert_not_called()
        mock_api_instance.apps.get.assert_called_with('a/b/c',
                                                      api=mock_api_instance)

    @patch(
        'sbg_cwl_upgrader.converter.cwl_converter.CWLConverterFacade._parse'
    )
    @patch(
        ('sbg_cwl_upgrader.converter.'
         'cwl_converter.CWLConverterFacade._load_input_cwl')
    )
    @patch('sevenbridges.Api')
    @patch('sevenbridges.Config', MagicMock())
    @patch('sys.stdout', MagicMock())
    @patch('sbg_cwl_upgrader.converter.cwl_converter.prompt_for_confirmation',
           MagicMock(return_value=False))
    def test_local_input_platform_output_update(
            self, mock_api, mock_load, mock_parse
    ):
        """
        Check if install_app is called if app does not exist
        """

        mock_app_wf1 = MagicMock(sevenbridges.App)
        mock_app_wf1.raw = {
            "id": "a/b/c",
            "class": "CommandLineTool",
            "cwlVersion": "sbg:draft-2"
        }
        mock_user = MagicMock(sevenbridges.User)
        mock_user.username = "foo"
        mock_api_instance = mock_api.return_value
        mock_api_instance.users.me.return_value = mock_user
        mock_api_instance.apps.get.side_effect = mock_app_get_not_found
        mock_parse.return_value = mock_app_wf1.raw
        mock_load.return_value = mock_app_wf1.raw
        CWLConverterFacade("a.cwl", output='a/b/c', validate=False,
                           decompose=False, update=True)

        mock_parse.assert_called()
        mock_api_instance.apps.create_revision.assert_not_called()
        mock_api_instance.apps.install_app.assert_called_with(
            'a/b/c', ANY, api=mock_api_instance
        )
        mock_api_instance.apps.get.assert_called_with(
            'a/b/c',
            api=mock_api_instance
        )
