import getpass
import time
from math import floor

import colorama
import keyring
from linode_api4 import (LinodeClient)
from linode_api4.objects.linode import Instance, Disk


class ResizeLinode:
    def __init__(self):
        self.key = self.get_api_key_keyring()
        self.client = LinodeClient(self.key)
        self.selected_id = None
        self.planned_disk_size: int = 30

        self.id_drive_to_shrink = 0
        self.target_size_gb = 0

    def set_api_key_keyring(self) -> None:
        """
        Put API key into local system keyring and return it
        On Linux: For best results, install dbus-python as a system package.
        :return: None
        """
        if self.key is not None:
            if input(colorama.Fore.RED + "API Key for Linode already found!\n"
                     + "Are you sure you want to create a new one? Y/N: ").strip().lower() != "y":
                quit()

        print(colorama.Style.RESET_ALL)
        print("Please create a new Access Token here with read_write access to \
              Linodes here: https://cloud.linode.com/profile/tokens")

        keyring.set_password("linode", "api_key", getpass.getpass(prompt="API key: "))
        print("API Key successfully saved!")

    def get_api_key_keyring(self) -> str:
        """
        Retrieve API key from local system keyring
        :return: password string
        """
        key: str = keyring.get_password("linode", "api_key")
        if key is None or key == "":
            self.set_api_key_keyring()
        else:
            return key

    def api_linode_list_instances(self) -> list:
        return list(self.client.linode.instances())

    def api_linode_list_available_instances(self) -> list:
        return list(self.client.linode.types())

    def api_linode_get_current_volumes(self) -> list:
        return Instance(self.client, self.selected_id).disks

    def api_linode_shutdown_instance(self):
        Instance(self.client, self.selected_id).shutdown()
        return

    def api_linode_get_disk_count(self) -> int:
        return len(self.api_linode_get_current_volumes())

    def api_linode_get_swap_size(self) -> int:
        return sum(disk.size for disk in self.api_linode_get_current_volumes() if disk.filesystem == "swap")

    def api_linode_get_disk_size(self) -> int:
        return sum(disk.size for disk in self.api_linode_get_current_volumes() if disk.filesystem != "swap")

    def api_linode_get_disk_total_size(self) -> int:
        return sum(disk.size for disk in self.api_linode_get_current_volumes())

    def api_linode_get_total_disk_size_gb(self) -> float:
        return self.convertToGigabyte(self.api_linode_get_disk_total_size())

    def api_linode_get_total_disk_size(self) -> float:
        """
        Get total size used by disk. If this sum is greater than the size of the instance that we want to
        change to, we must first resize the primary disk so it fits the size of the intended instance.
        :return: Total size of Disk for Linode Instance
        """
        return self.api_linode_get_swap_size() + self.api_linode_get_disk_size()

    def api_linode_get_first_disk_size(self) -> int:
        for disk in self.api_linode_get_current_volumes():
            if disk.filesystem != "swap":
                return int(floor(disk.size))

    def api_linode_get_first_disk_id(self):
        for disk in self.api_linode_get_current_volumes():
            if disk.filesystem != "swap":
                return disk.id

    def api_linode_get_status(self) -> bool:
        return Instance(self.client, self.selected_id).status != "offline"

    def shrink_volume(self) -> None:
        if self.id_drive_to_shrink == 0 or self.target_size_gb == 0:
            print("ERROR")
            exit()
        if self.api_linode_get_status():
            self.api_linode_shutdown_instance()

            while self.api_linode_get_status():
                time.sleep(8)
                print("Waiting for instance to shutdown")

        Disk(client=self.client, id=self.id_drive_to_shrink, parent_id=self.selected_id).resize(self.target_size_gb)
        print("Resizing. . .")
        for i in range(0, 20):
            print(Instance(self.client, self.selected_id).status)
            time.sleep(8)

    def shrink_drive(self) -> None:
        if self.planned_disk_size != 0:
            size_delta = self.api_linode_get_total_disk_size_gb() - self.planned_disk_size
            if size_delta > 0:
                if input("Your current disk is {0}GB, however your chosen instance is {1}GB. \n\
You must shrink the drive by {2}GB before continuing.\n\
Note this may take a long time and the Linode instance must be powered down! Y/N?: ".format(
                    self.api_linode_get_total_disk_size_gb(), self.planned_disk_size,
                    size_delta)).strip().lower() == "y":
                    if self.api_linode_get_disk_count() > 2:
                        print("More than 2 drives found! Will shrink first-non Swap drive only!")
                    self.id_drive_to_shrink = self.api_linode_get_first_disk_id()
                    print("id to shrink", self.id_drive_to_shrink)
                    self.target_size_gb = self.api_linode_get_first_disk_size() - self.convertToMegabyte(size_delta)

                    print("sum", self.api_linode_get_first_disk_size(), "minus", self.convertToMegabyte(size_delta))
                    print(self.target_size_gb)
                    self.shrink_volume()
                    # TODO
                else:
                    quit()

    def convertToMegabyte(self, gb):
        return floor(gb * 1024)

    def convertToGigabyte(self, mb: int):
        return mb / 1024


resize = ResizeLinode()
print(resize.shrink_drive())
