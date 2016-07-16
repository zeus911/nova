from nova.core.stash.decrypt import Decrypt
from nova.core.stash.encrypt import Encrypt
from tests.cli.utils import NovaTestCase, TestManagerProvider

try:
    import mock
except ImportError:
    import unittest.mock as mock


class NovaStashTestCase(NovaTestCase):

    def test_encrypt(self):
        manager_provider = TestManagerProvider()
        Encrypt(
            'test-key',
            'test-value',
            manager_provider
        )

    def test_decrypt(self):
        manager_provider = TestManagerProvider()
        Decrypt(
            'test-key',
            manager_provider
        )
