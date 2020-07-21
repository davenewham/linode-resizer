linode-resizer
==============

[WIP] A program to resize Linode Instances to smaller/larger ones.


### Authentication
For authentication you must make an Access Token here with read_write access to Linodes here [https://cloud.linode.com/profile/tokens](https://cloud.linode.com/profile/tokens)

### Dependencies

`pip install colorama keyring`

On Linux it is recommended you install dbus-python as a system package for keyring.

`sudo apt-get install dbus-python`

### How to Run
`python linode-resizer.py`

On first run you will be prompted for your access token. It will be saved to your local keyring for future use. 

### To Do:
* Allow shrinking to smaller disks (-swap space)
* Handle errors better
* Allow CLI interface
* Check if resizing to same size
* Create simple Unit Test
* Create small documentation using Sphinx
