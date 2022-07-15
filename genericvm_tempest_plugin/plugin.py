"""
Copyright 2015
All Rights Reserved.

   Licensed under the Apache License, Version 2.0 (the "License"); you may
   not use this file except in compliance with the License. You may obtain
   a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
   License for the specific language governing permissions and limitations
   under the License.
"""

import os

from tempest.test_discover import plugins

from genericvm_tempest_plugin import config as genericvm_config


class GenericVMTempestPlugin(plugins.TempestPlugin):
    """
    Tempest set of tests to check vm created from defined image
    """
    def load_tests(self):
        """
        Make tests available in tempest
        :return: path to the test
        """
        base_path = os.path.split(os.path.dirname(
            os.path.abspath(__file__)))[0]
        test_dir = "genericvm_tempest_plugin/tests"
        full_test_dir = os.path.join(base_path, test_dir)
        return full_test_dir, base_path

    def register_opts(self, conf):
        """
        Defines set of options and a section in tempest config
        :param conf: config
        :return:
        """
        conf.register_group(genericvm_config.genericvm_group)
        conf.register_opts(genericvm_config.GenericvmGroup, group='genericvm')
        conf.register_opt(genericvm_config.service_option,
                          group='service_available')

    def get_opt_lists(self):
        """
        Used to list options available for the plugin
        :return: list of options
        """
        return [('genericvm', genericvm_config.GenericvmGroup),
                ('service_available', [genericvm_config.service_option])]
