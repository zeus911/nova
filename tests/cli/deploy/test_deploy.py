from nova.cli.controllers.deploy.deploy import INCORRECT_ARGS_USAGE
from nova.cli.main import get_test_app
from nova.core import NovaError
from tests.cli.utils import NovaTestCase


class NovaDeployTestCase(NovaTestCase):

    def test_deploy_no_args(self):
        with get_test_app(argv=['deploy']) as app:
            try:
                app.run()
            except NovaError as e:
                self.assertEqual(e.msg, INCORRECT_ARGS_USAGE)
