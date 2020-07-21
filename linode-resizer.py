import requests
import getpass

import colorama
import keyring


colorama.init()


def set_api_key_keyring() -> None:
    """
    Put API key into local system keyring.
    On Linux: For best results, install dbus-python as a system package.
    :return: None
    """
    if get_api_key_keyring() is not None:
        if input(colorama.Fore.RED + "API Key for Linode already found!\n"
                 + "Are you sure you want to create a new one? Y/N: ").strip().lower() != "y":
            quit()

    print(colorama.Style.RESET_ALL)
    print(
        "Please create a new Access Token here with read_write access to Linodes here: https://cloud.linode.com/profile/tokens")
    keyring.set_password("linode", "api_key", getpass.getpass(prompt="API key: "))
    # TODO: error handle
    print("API Key successfully saved!")


def get_api_key_keyring() -> str:
    """
    Retrieve API key from local system keyring
    :return: password string
    """
    return keyring.get_password("linode", "api_key")


def _headers() -> dict:
    return {
        'Content-Type': 'application/json',
        'Authorization': "Bearer {}".format(get_api_key_keyring())
    }


def _getInfo(instance):
    return instance["id"], instance["label"], instance["region"], instance["type"]


def _getInstancesAvailable(instance):
    return instance["id"], instance["label"], instance["price"]["monthly"]


def _fmt_tuple(txt: tuple) -> str:
    return ' '.join(map(str, txt))


def list_linode(page=1, page_size=100):
    # TODO: Naively assumes no more than 100 linode instances 100 for now.
    url = "https://api.linode.com/v4/linode/instances/"
    res_json = (_handle(requests.get(url=url, data=None, headers=_headers()))).json()
    # print(res_json)
    max = len(res_json["data"])
    count = 0

    for i in res_json["data"]:
        count = count + 1
        print(str(count) + ":" + colorama.Fore.BLUE, _fmt_tuple(_getInfo(i)), colorama.Style.RESET_ALL)

    # Select Linode To Resize
    selected_instance = int(input("Which Instance would you like to resize?: ").strip()) - 1
    linode_type = list_linode_sizes()
    if input("Are you sure you want to resize " +
             res_json["data"][selected_instance]["label"] +
             " to: " + linode_type + "? Y/N: ").strip().lower() != "y":
        quit()
    else:
        linode_id = res_json["data"][selected_instance]["id"]

        _handle(resize_linode(linode_id, linode_type)).json()
        print("Linode is scheduled for resizing. The Linode will now stop and start!")


def list_linode_sizes() -> str:
    """

    :return: The ID String representing the Linode Type.
    """
    url = "https://api.linode.com/v4/linode/types"
    res_json = (_handle(requests.get(url=url, headers=_headers()))).json()
    count = 0
    for i in res_json["data"]:
        count = count + 1
        print(str(count) + ":" + colorama.Fore.BLUE, _fmt_tuple(_getInstancesAvailable(i)), colorama.Style.RESET_ALL)

    selected_linode_size = int(input("Which Linode Type would you like to change to?: ").strip()) - 1
    return res_json["data"][selected_linode_size]["id"]


def _bool_to_int(input_bool: bool) -> str:
    if input_bool:
        return "true"
    else:
        return "false"


def resize_linode(linodeID: int, type: str, allow_auto_disk_resize: bool = True) -> requests.models.Response:
    """
    Resize Linode instance to smaller or greater size.
    If allow_auto_disk_resize is set to true, you must ensure that it fits on the smaller drive

    :param linodeID: ID Number of the Linode to resize.
    :param type: The ID String representing the Linode Type.
    :param allow_auto_disk_resize: Bool Automatically resize disks when resizing a Linode.
    :return: Response code from request. 200 OK, 404 No URL,
    """
    url = "https://api.linode.com/v4/linode/instances/{}/resize".format(linodeID)
    data = {"type": "{}".format(type), "allow_auto_disk_resize": allow_auto_disk_resize}

    return requests.post(url=url, json=data, headers=_headers())


def _handle(res: requests.models.Response):
    status_code: int = int(res.status_code)

    if status_code == 401:
        # We are un-authorized. Prompt for API key again
        print("Error! Invalid API Key")
        set_api_key_keyring()
    elif status_code == 200:
        return res
    elif status_code == 400:
        # Error List
        # "Linode busy." - currently resizing
        # Resizing a disk requires you to power your Linode off, if it is currently in use by your Linode. Shrinking a disk takes longer than increasing its size.
        print("Bad Request!")
        print(res.content, "\n")
    else:
        print("Error: Did not handle: ", res.status_code, " response")


def show_menu() -> str:
    return ("\
     1. Resize Linode Instances\n\
     2. Set Linode API Key\n\
     3. Exit\n\
Choose an Option: ")


if __name__ == '__main__':
    user_selection: int = 0

    while user_selection != 3:
        user_selection: int = int(input(show_menu()).strip())
        if user_selection == 1:
            list_linode()
            pass
        elif user_selection == 2:
            set_api_key_keyring()
            pass
