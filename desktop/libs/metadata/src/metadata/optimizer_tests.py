#!/usr/bin/env python
# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import json

from nose.plugins.skip import SkipTest
from nose.tools import assert_equal, assert_true

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from hadoop.pseudo_hdfs4 import is_live_cluster
from desktop.lib.django_test_util import make_logged_in_client
from desktop.lib.test_utils import add_to_group, grant_access

from metadata.optimizer_client import OptimizerApi, is_optimizer_enabled


LOG = logging.getLogger(__name__)


class TestOptimizerApi(object):

  @classmethod
  def setup_class(cls):

    if not is_optimizer_enabled():
      raise SkipTest

    cls.client = make_logged_in_client(username='test', is_superuser=False)
    cls.user = User.objects.get(username='test')
    add_to_group('test')
    grant_access("test", "test", "metadata")
    grant_access("test", "test", "optimizer")

    cls.api = OptimizerApi()


  @classmethod
  def teardown_class(cls):
    cls.user.is_superuser = False
    cls.user.save()


  def test_api_create_product(self):
    resp = self.api.create_product()

    assert_equal('success', resp['status'], resp)


  def test_api_add_email_to_product(self):
    resp = self.api.add_email_to_product()

    assert_equal('success', resp['status'], resp)


  def test_api_authenticate(self):
    resp = self.api.authenticate()

    assert_true(resp['token'], resp)
    assert_equal('success', resp['status'], resp)


  def test_api_get_status(self):
    resp = self.api.authenticate()
    token = resp['token']
   
    resp = self.api.get_status(token=token)

    assert_equal('success', resp['status'], resp)
    assert_true('filesFinished' in resp['details'], resp)
    assert_true('filesProcessing' in resp['details'], resp)
    assert_true('finished' in resp['details'], resp)


  def test_api_upload(self):
    resp = self.api.authenticate()
    token = resp['token']

    queries = [
        "select emps.id from emps where emps.name = 'Joe' group by emps.mgr, emps.id;",
        "select emps.name from emps where emps.num = 007 group by emps.state, emps.name;",
        "select Part.partkey, Part.name, Part.type from Part where Part.yyprice > 2095",
        "select Part.partkey, Part.name, Part.mfgr FROM Part WHERE Part.name LIKE '%red';",
        "select count(*) as loans from account a where a.account_state_id in (5,9);",
        "select orders.key, orders.id from orders where orders.price < 9999",
        "select mgr.name from mgr where mgr.reports > 10 group by mgr.state;"
    ]

    resp = self.api.upload(token=token, queries=queries)
    assert_equal('success', resp['status'], resp)
