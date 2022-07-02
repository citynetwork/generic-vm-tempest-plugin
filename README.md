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
* kenrel_mod - defines a list of kernel modules required
to be present. Use period to separate values. lsmod used
* flavor - desired flavor to use during the image testing
If omitted global image_ref is used.
* username - username to be used to login to the server.
If omitted used globally defined username.
* with_volume - whether to create volume-based server or
not.
* check_getpass - whether to look for getpass binary.

Additionaly we can set nvgrid service in service_available 
section. This will add a verification for the nvidia grid
hardware. Available pci devices, necessary host records,
additional kernel modules.

* nvgrid - Bool. Default to true

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
