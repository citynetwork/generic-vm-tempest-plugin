"""
Genericvm tempest plugin
Copyright 2022 City Network International AB

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

from tempest import config
from tempest.common import waiters
from tempest.lib import exceptions
from tempest.lib.common.utils import test_utils
from tempest.scenario import manager

CONF = config.CONF


class GenericvmTestScenario(manager.ScenarioTest):
    """ This test created to verify DIB image work and consistency.
    It tests the following behaviour:
    - checks image availability
    - creates ssh keypair
    - creates a server from defined image and created ssh-keypair.
    - login to a server using ssh
    - verify disk size
    - verify defined script presence
    - verify kernel modules availability
    - verify pci devices availability
    - verify nvidia drivers work
    """
    credentials = ['primary']

    def create_and_add_security_group_to_server(self, server):
        """function that creates and assign a security group

        Creates a security group which allows to make a connection.
        Assign it to the server provided. This is necessary to let
        testing script login to the server using ssh.

        :type server: openstack.compute.v2.server.Server
        :param server: id of the server to assign security group to.

        :return: void
        """
        secgroup = self.create_security_group()
        self.servers_client.add_security_group(server['id'],
                                               name=secgroup['name'])
        self.addCleanup(self.servers_client.remove_security_group,
                        server['id'], name=secgroup['name'])

        def wait_for_secgroup_add():
            """
            Checks that security group is assigned to the server
            :return: bool
            """
            body = (self.servers_client.show_server(server['id'])
                    ['server'])
            return {'name': secgroup['name']} in body['security_groups']

        if not test_utils.call_until_true(wait_for_secgroup_add,
                                          CONF.compute.build_timeout,
                                          CONF.compute.build_interval):
            msg = (f"Timed out waiting for adding security group \
            {secgroup['id']} to the server {server['id']}")
            raise exceptions.TimeoutException(msg)

    def get_port_id(self, ip_address):
        """
        Get port id without os_admin. os_primary is used instead
        """
        port_client = self.os_primary.ports_client
        # floating_client = self.os_primary.floating_ips_client
        available_ports = port_client.list_ports()
        # import epdb; epdb.serve()
        for port in available_ports['ports']:
            for fixed_ip in port['fixed_ips']:
                if fixed_ip['ip_address'] == ip_address:
                    return port['id']
        return None

    def create_floating_ip(self, server):
        """
        Non admin floating IP creation
        """
        floating_client = self.os_primary.floating_ips_client
        ip4 = self.get_ip_address(server)
        port_id = self.get_port_id(ip4)
        # import epdb; epdb.serve()
        external_network_id = CONF.network.public_network_id
        floatingip_kwargs = {
            'floating_network_id': external_network_id,
            'port_id': port_id,
            'tenant_id': server.get('project_id') or server['tenant_id'],
            'fixed_ip_address': ip4}
        result = floating_client.create_floatingip(**floatingip_kwargs)
        floating_ip = result['floatingip']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        floating_client.delete_floatingip,
                        floating_ip['id'])
        return floating_ip

    def get_ip_address(self, server):
        addresses = server['addresses'][
            CONF.compute.fixed_network_name]
        for address in addresses:
            return address['addr']
        raise exceptions.ServerUnreachable(server_id=server['id'])

    def test_minimum_image_validity_scenario(self):
        """
        Main image test case.
        """

        keypair = self.create_keypair()
        kernel_modules = CONF.genericvm.kernel_mod
        pci_devices = CONF.genericvm.get('pci_devices', [])
        if CONF.service_available.get('nvgrid', False):
            kernel_modules.extend(['nvidia', 'nvidia_drm'])
            pci_devices.extend(["3D controller"])
            check_nv_sni = True
        else:
            check_nv_sni = CONF.genericvm.check_nv_sni
        create_args = {
            'name': 'genericvm_test',
            'image_id': CONF.genericvm.get('image_id',
                                           CONF.compute.get('image_ref')),
            'key_name': keypair['name'],
            'validatable': False,
            'volume_backed': CONF.genericvm.with_volume,
            'flavor': CONF.genericvm.get(
                'flavor', CONF.compute.get('flavor_ref'))}

        server = self.create_server(**create_args)
        servers = self.servers_client.list_servers()['servers']
        self.assertIn(server['id'], [x['id'] for x in servers])

        if (CONF.network_feature_enabled.floating_ips and
                CONF.network.floating_network_name):
            floating_ip = self.create_floating_ip(server)
            waiters.wait_for_server_floating_ip(
                self.servers_client, server, floating_ip)
            ssh_ip = floating_ip['floating_ip_address']
        else:
            ssh_ip = self.get_server_ip(server)

        self.create_and_add_security_group_to_server(server)
        linux_client = self.get_remote_client(
            ssh_ip,
            username=CONF.genericvm.get('username',
                                        CONF.validation.get('image_ssh_user',
                                                            'clouduser')),
            private_key=keypair['private_key'],
            server=server)
        if CONF.genericvm.check_getpass:
            msg = 'getpass.sh file is missing in image'
            getpass_present = linux_client.exec_command(
                "test -f /etc/cloud/getpass.sh && echo 1")
            self.assertEqual(1, int(getpass_present), msg)
        filesystem_size = linux_client.exec_command(
            "df | grep '/dev/sda1' | awk '{ print $2 }'")
        self.assertTrue(CONF.genericvm.fs_size < int(filesystem_size))

        lsof_run = linux_client.exec_command("lsmod")
        the_modules = [mod.split()[0]
                       for mod in lsof_run.split("\n")[1:] if mod]
        mod_assert_text = "module {} is missing! Available modules are:\n{}"
        for module in kernel_modules:
            self.assertTrue(module in the_modules,
                            mod_assert_text.format(module, the_modules))

        lspci_run = linux_client.exec_command("lspci -m")
        found_pci_devices = []
        for device in lspci_run.split('\n'):
            try:
                found_pci_devices.append(device.split('"')[1])
            except IndexError:
                pass
        for dev_class in pci_devices:
            self.assertIn(dev_class, found_pci_devices,
                          message='Required PCI device is not available')

        if check_nv_sni:
            # Rises exception if the exit code is not 0. When no vide card.
            linux_client.exec_command("nvidia-smi -L")
