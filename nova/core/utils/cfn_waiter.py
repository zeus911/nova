from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import os
import json
from botocore.waiter import WaiterModel, create_waiter_with_client
from nova.core import utils


class CloudformationWaiter(object):

    def __init__(self, client):
        waiter_json_filename = os.path.join(utils.__path__[0], 'cfn-waiters-2.json')
        with open(waiter_json_filename, 'r') as waiter_json_file:
            self.waiter_json_model = json.load(waiter_json_file)
        self.waiter_model = WaiterModel(self.waiter_json_model)
        self.waiter = create_waiter_with_client('StackAvailable', self.waiter_model, client.meta.client)
