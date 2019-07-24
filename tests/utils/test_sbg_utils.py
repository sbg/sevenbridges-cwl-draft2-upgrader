from unittest import TestCase
from sbg_cwl_upgrader.sbg_utils import get_endpoint


class TestSBGUtils(TestCase):
    def test_get_endpoint_platforms(self):
        """
        Assure all the platforms remain at get_endpoint
        """
        for platform in ["igor", "cgc", "eu", "cn",
                         "cavatica", "f4c", "sbpla", "default"]:
            self.assertTrue(get_endpoint(platform))

    def test_get_endpoint_unknown_platform(self):
        """
        Assure unknown platfrom raises ValueError
        """
        with self.assertRaises(ValueError):
            get_endpoint('foo bar buzz')
