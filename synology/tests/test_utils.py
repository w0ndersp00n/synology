from unittest import TestCase


class TestUtils(TestCase):
    def endpoint_is_str(self):
        endpoint = 'toto'
        self.assertTrue(isinstance(endpoint, str))
