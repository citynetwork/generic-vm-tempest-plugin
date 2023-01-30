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

from oslo_config import cfg

service_option = cfg.BoolOpt('nvgrid',
                             default=False,
                             help="Whether or not nvidia grid is available")

genericvm_group = cfg.OptGroup(
    name="genericvm",
    title="Image testing variables"
)

GenericvmGroup = [
    cfg.IntOpt("fs_size", default=45000000,
               help="Expected filesystem size should be more than..."),
    cfg.ListOpt('kernel_mod', default=['virtio_net', 'virtio_scsi'],
                help="Expected list of loaded kernel modules"),
    cfg.StrOpt('flavor', help="Flavor to use for the image creation"),
    cfg.BoolOpt('with_volume', default=True,
                help='Use volume?'),
    cfg.StrOpt('username', default='clouduser', help='VM login username'),
    cfg.StrOpt('image_id', help='An image to use'),
    cfg.BoolOpt('check_getpass', default=False,
                help='Do we need to look for getpass binary?'),
    cfg.ListOpt('pci_devices', default=[],
                help='expected list of pci devices classes.'),
    cfg.BoolOpt('check_nv_sni', default=False,
                help='query nvidia-sni for the vide card and driver presence'),
]
