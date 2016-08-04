from six import StringIO
from Crypto.Util.py3compat import b
from botocore.response import StreamingBody

from cement.utils import test
from nova.cli.main import NovaApp
from nova.core.managers.version_manager import VersionManager

try:
    import mock
except ImportError:
    import unittest.mock as mock

KMS_GENERATED_KEY_TEST = {
    'Plaintext': b('n\xde\xe3\xd7\xdb\x8d\x93\xb6\xb7\xcc\x11l\xb6<\xe2\x99\xc66z\x181l\xf7\x83&\x9f\xaa\x8e\x1dHHLW\x91g[\xd2\x0bQ>b\xa7\x80y#\xe8\xb3\xa38\xb3}V@\xad\x16\xdc\x8dA-\xa0\xd8Z\x9bn'),
    'CiphertextBlob': b('\n \xc4N\x1e\x91\x89\xda\xf0\xb0\xd3\xef~\xa8\xc9\xeb\xfc\xea\xd6\x01\xde\xab@yR^\x82\x11\x18\x88\xd2\xc8OZ\x12\xcb\x01\x01\x01\x01\x00x\xc4N\x1e\x91\x89\xda\xf0\xb0\xd3\xef~\xa8\xc9\xeb\xfc\xea\xd6\x01\xde\xab@yR^\x82\x11\x18\x88\xd2\xc8OZ\x00\x00\x00\xa20\x81\x9f\x06\t*\x86H\x86\xf7\r\x01\x07\x06\xa0\x81\x910\x81\x8e\x02\x01\x000\x81\x88\x06\t*\x86H\x86\xf7\r\x01\x07\x010\x1e\x06\t`\x86H\x01e\x03\x04\x01.0\x11\x04\x0c\xc41\xb6g\x13\xb1#-\x07\xa9l2\x02\x01\x10\x80[ \xe1\xb2\xf7}\xd3\xceq\xdb<\xa7\xc1\xef\xdb(3Q\xd5\xef\xc7\x12\x00.\xb5\xb1\x1c\xc3\x81\x0cT\x19\x96o\x92 iD\xfb\xa8\xd7\xc3U)\x10\xa0+At\xba\xd3*\xac \xc8\x93\xccWz\xb2e\xba\x02\xb9[\x92K\x1e\xf2\x8a]=\xfckc\x04(\xf3H\xfe)pe\xe3\x95t\xc3:\x06<\xeeZ')
}

STASHED_TEST = {
    'Body': StreamingBody(StringIO('vVz9oEEi5f18toTrP4r9ATSRd5E='), 28),
    'Metadata': {
        'hmac': '3da9fb2aa806502299d22a829b7cf3360c9875f102c3630deaeffbdd8c87b34c',
        'encryption-key': 'CiAAPMQUTNJa7ldugKQ3+4kpiHxFEcau28/xznVisaySexLLAQEBAQB4ADzEFEzSWu5XboCkN/uJKYh8RRHGrtvP8c51YrGsknsAAACiMIGfBgkqhkiG9w0BBwaggZEwgY4CAQAwgYgGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMwJNV0/lNTqa39dO4AgEQgFv1SrPvLh6OPYDjgRamKE/mXMrygZSE3QK31jPDZw+SM4Jo7b8SgBkkQCX3fGRnjUZPEeAMF5VJ13TWIc6B60ag21FePXrQYdQEyIPDJ6aN12kJABGWhwg46ztp'
    }
}

DECRYPT_TEST_RESULT = {
    'Plaintext': b("\xc5\xfe4N\xc2\xf37\xef\xae\xc6wo\xa0\x8e\x90\xa94(O\x08BSZu\xc2[\xbd\x85'\xa2\x8e(\xa9^\x1dMS\xcd\xd9iF\xbf\xcba\xebo\xea\xfc4\xc7\xc9\xb5\xf1\xec)\t!\xad]\x96\xac\xcca\xf1")
}


class NovaTestCase(test.CementTestCase):
    app_class = NovaApp

    def setUp(self):
        super(NovaTestCase, self).setUp()


class TestManagerProvider(object):

    def __init__(self):
        patcher = mock.patch('nova.core.managers.aws_manager.AwsManager')
        self.mock_aws_manager = patcher.start()
        type(self.mock_aws_manager).account_alias = mock.PropertyMock(return_value='test-account')
        self.mock_aws_manager.s3_get.return_value = STASHED_TEST
        self.mock_aws_manager.s3_head.return_value = None
        self.mock_aws_manager.kms_generate_data_key.return_value = KMS_GENERATED_KEY_TEST
        self.mock_aws_manager.kms_decrypt.return_value = DECRYPT_TEST_RESULT

        self.mock_docker_manager = mock.MagicMock(name='docker_manager')

        version_patcher = mock.patch('nova.core.managers.version_manager.VersionManager')
        self.mock_version_manager = version_patcher.start()
        type(self.mock_version_manager).current_version = mock.MagicMock(return_value='0.0.1')

    def aws_manager(self, profile, region):
        return self.mock_aws_manager

    def docker_manager(self):
        return self.mock_docker_manager

    def version_manager(self):
        return self.mock_version_manager
