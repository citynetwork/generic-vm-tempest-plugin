from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import exceptions
from tempest.scenario import manager

CONF = config.CONF


class GenericvmTestScenario(manager.ScenarioTest):
    """ This test created to verify DIB image work and consistency.
    It tests the following behaviour:
    - checks image availability
    - check image meta is set
    - creates ssh keypair
    - creates a server from defined image and created ssh-keypair.
    - login to a server using ssh
    - verify disk size
    - verify defined script presence
    """
    credentials = ['primary']

    def create_and_add_security_group_to_server(self, server):
        secgroup = self.create_security_group()
        self.servers_client.add_security_group(server['id'],
                                               name=secgroup['name'])
        self.addCleanup(self.servers_client.remove_security_group,
                        server['id'], name=secgroup['name'])

        def wait_for_secgroup_add():
            body = (self.servers_client.show_server(server['id'])
                    ['server'])
            return {'name': secgroup['name']} in body['security_groups']

        if not test_utils.call_until_true(wait_for_secgroup_add,
                                          CONF.compute.build_timeout,
                                          CONF.compute.build_interval):
            msg = ('Timed out waiting for adding security group %s to server '
                   '%s' % (secgroup['id'], server['id']))
            raise exceptions.TimeoutException(msg)

    def test_minimum_image_validity_scenario(self):
        keypair = self.create_keypair()
        kernel_modules = CONF.genericvm.kenrel_mod
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

        ssh_ip = self.get_server_ip(server)
        self.create_and_add_security_group_to_server(server)
        self.linux_client = self.get_remote_client(
            ssh_ip,
            username=CONF.genericvm.get('username',
                                        CONF.validation.get('image_ssh_user',
                                                            'clouduser')),
            private_key=keypair['private_key'],
            server=server)
        if CONF.genericvm.check_getpass:
            msg = 'getpass.sh file is missing in image'
            getpass_present = self.linux_client.exec_command(
                "test -f /etc/cloud/getpass.sh && echo 1")
            self.assertEqual(1, int(getpass_present), msg)
        filesystem_size = self.linux_client.exec_command(
            "df | grep '/dev/sda1' | awk '{ print $2 }'")
        self.assertTrue(CONF.genericvm.fs_size < int(filesystem_size))

        lsof_run = self.linux_client.exec_command("lsmod")
        the_modules = [mod.split()[0]
                       for mod in lsof_run.split("\n")[1:] if mod]
        mod_assert_text = "module {} is missing! Available modules are:\n{}"
        for module in kernel_modules:
            self.assertTrue(module in the_modules,
                            mod_assert_text.format(module, the_modules))

        lspci_run = self.linux_client.exec_command("lspci -m")
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
            self.linux_client.exec_command("nvidia-smi -L")
