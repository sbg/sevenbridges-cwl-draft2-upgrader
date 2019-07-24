from unittest import TestCase
from sbg_cwl_upgrader.cwl_utils import (cwl_ensure_dict,
                                        cwl_ensure_array,
                                        get_abs_path)
import unittest
import sys


class TestCWLTyping(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.in_list = [
            {
                "id": "a",
                "type": "string"
            },
            {
                "id": "b",
                "type": "string"
            },
            {
                "id": "c",
                "type": "File"
            }
        ]
        cls.in_dict = {
            "a": {
                "type": "string"
            },
            "b": {
                "type": "string"
            },
            "c": {
                "type": "File"
            }
        }

    def test_list_to_dict(self):
        """
        Test list to dict conversion
        """
        out_dict = cwl_ensure_dict(self.in_list, id_key="id")
        self.assertIsInstance(out_dict, dict)
        self.assertEqual(out_dict, self.in_dict)

    def test_dict_to_dict(self):
        """
        Test that cwl_ensure_dict keeps dict
        """
        self.assertEqual(self.in_dict, cwl_ensure_dict(self.in_dict, 'id'))

    def test_dict_to_list(self):
        """
        Test dict to list conversion
        """
        out_list = cwl_ensure_array(self.in_dict, id_key="id")
        self.assertIsInstance(out_list, list)
        self.assertEqual(out_list, self.in_list)

    def test_list_to_list(self):
        """
        Test that cwl_ensure_array keeps list
        """
        self.assertEqual(self.in_list, cwl_ensure_array(self.in_list, 'id'))


class TestGetAbsPath(TestCase):
    @unittest.skipIf(sys.platform == "Windows", "Skip path check on windows.")
    def test_abs_path_from_here(self):
        input_ = "c"
        base = "/a"
        self.assertEqual(get_abs_path(input_, base),
                         "/a/c")

    @unittest.skipIf(sys.platform == "Windows", "Skip path check on windows.")
    def test_abs_path_from_here_dot(self):

        input_ = "./c"
        base = "/a"
        self.assertEqual(get_abs_path(input_, base),
                         "/a/c")

    @unittest.skipIf(sys.platform == "Windows", "Skip path check on windows.")
    def test_full_path(self):
        input_ = "/c"
        base = "/a"
        self.assertEqual(get_abs_path(input_, base),
                         "/c")

    @unittest.skipIf(sys.platform == "Windows", "Skip path check on windows.")
    def test_two_dots(self):
        input_ = "../c"
        base = "/a"
        self.assertEqual(get_abs_path(input_, base),
                         "/c")
