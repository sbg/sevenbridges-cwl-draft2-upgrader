from unittest import TestCase
from sbg_cwl_upgrader.converter.workflow import CWLWorkflowConverter


class TestCWLWorkflowConverter(TestCase):

    def test_handle_source_string(self):
        d2_source = '#foo'
        self.assertEqual(CWLWorkflowConverter.handle_source(d2_source),
                         ['foo'])

    def test_handle_source_list(self):
        d2_source = ['#foo', '#foo/bar']
        self.assertEqual(CWLWorkflowConverter.handle_source(d2_source),
                         ['foo', 'foo/bar'])
