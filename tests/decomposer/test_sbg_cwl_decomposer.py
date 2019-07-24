from unittest import TestCase
from sbg_cwl_upgrader.decomposer.sbg_cwl_decomposer import main
from unittest.mock import patch, ANY, MagicMock


class TestArgParser(TestCase):
    @patch('logging.basicConfig', MagicMock())
    @patch(
        'sbg_cwl_upgrader.decomposer.sbg_cwl_decomposer.breakdown_wf_local'
    )
    def test_multiple_local_apps(self, mock_breakdown):
        """
        Test all apps are decomposed.
        """
        main(['-a', 'a.cwl', '-a', 'b.cwl'])
        mock_breakdown.assert_any_call(
            'b.cwl'
        )
        mock_breakdown.assert_any_call(
            'a.cwl'
        )

    @patch('logging.basicConfig', MagicMock())
    @patch(
        'sbg_cwl_upgrader.decomposer.sbg_cwl_decomposer.breakdown_wf_sbg'
    )
    @patch('sbg_cwl_upgrader.decomposer.sbg_cwl_decomposer.init_api',
           MagicMock())
    @patch('sbg_cwl_upgrader.sbg_utils.sbg.Api.apps.get', MagicMock())
    def test_multiple_platform_apps(self, mock_breakdown):
        """
        Test all apps are decomposed.
        """
        main(['-a', 'a/b/c', '-a', 'a/b/d'])
        mock_breakdown.assert_any_call(
            'c', 'a/b', ANY, ANY
        )
        mock_breakdown.assert_any_call(
            'd', 'a/b', ANY, ANY
        )
