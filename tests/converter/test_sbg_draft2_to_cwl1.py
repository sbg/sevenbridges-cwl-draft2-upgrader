from unittest import TestCase
from sbg_cwl_upgrader.converter.sbg_draft2_to_cwl_1_0 import (
    main
)
from unittest.mock import patch, MagicMock


class TestArgParser(TestCase):
    @patch('logging.basicConfig', MagicMock())
    @patch(
        'sbg_cwl_upgrader.converter.sbg_draft2_to_cwl_1_0.CWLConverterFacade'
    )
    def test_optional_defaults(self, mock_facade):
        main(['--input', 'a.cwl', '--output', 'b.cwl'])
        mock_facade.assert_called_once_with(
            app_revision=None,
            decompose=False,
            endpoint=None,
            input_='a.cwl',
            output='b.cwl',
            platform='igor',
            profile='default',
            token=None,
            update=False,
            validate=False
        )

    @patch('logging.basicConfig', MagicMock())
    @patch(
        'sbg_cwl_upgrader.converter.sbg_draft2_to_cwl_1_0.CWLConverterFacade'
    )
    def test_shorthand_inputs(self, mock_facade):
        main(['-i', 'a.cwl', '-o', 'b.cwl', '-u', '-d', '-v', '-r', '2'])
        mock_facade.assert_called_once_with(
            app_revision=2,
            decompose=True,
            endpoint=None,
            input_='a.cwl',
            output='b.cwl',
            platform='igor',
            profile='default',
            token=None,
            update=True,
            validate=True
        )
