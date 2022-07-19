Tempest plugin for the image verification
---------------

This directory contains Tempest tests to cover cloud
image verification. Image work in the cloud is not just
an ability to launch the server and being able to access
it from the network. Sometimes you rely on the hardware
which should be available in virtual machine and such
hardware along with the kernel modules might be a part of
the image. Sometimes you need to make sure that your
scripts made correct changes after the first boot.

Config options
---------------

Optional variables are set in genericvm group:
* fs_size - expected size for the vm filesystem. T check
growpart and allocated volume. Define size in bytes.
* kernel_mod - defines a list of kernel modules required
to be present. Use period to separate values. lsmod used
* flavor - desired flavor to use during the image testing
If omitted global image_ref is used.
* username - username to be used to login to the server.
If omitted used globally defined username.
* with_volume - whether to create volume-based server or
not.
* check_getpass - whether to look for getpass binary.
* pci_devices - comma separated list of pci devices classes
which must present in virtual machine. For example 
"3D controller" or "SCSI storage controller". Double quotas
are required to be present.
* check_nv_sni - boolean, defines whether to try nvidia
drivers and check video card availability.

Additionally, it is possible to set nvgrid service in service_available section.
This will add a verification for the nvidia grid hardware. Available pci
devices, necessary host records, additional kernel modules. It is equivalent to
the following options list:
* check_nv_sni: True
* pci_devices: "3D controller"
* kernel_mod: kernel_mod,nvidia_drm
Values of pci_devices and kernel_mod would be appended to the list from config.

Running the tests
---------------

In order to run test you will need to have a tempest
installed and configured. You will also need python build,
pbr and build-tools to build plugin package. 

```
# git clone https://github.com/citynetwork/generic-vm-tempest-plugin
# cd generic-vm-tempest-plugin
# python -m build
# pip install dist/generic...whl
# tempest run --regex GenericImageTestScenario
```
