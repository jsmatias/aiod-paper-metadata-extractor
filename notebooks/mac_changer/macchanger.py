import getpass
import pexpect
import optparse
import re
import subprocess
from generate_mac import generate_mac


ORIGINAL_MAC_ADDRESSES = {}

password = ""


def get_stored_mac(interface):
    mac = ORIGINAL_MAC_ADDRESSES[interface]
    return mac


def get_current_ip(interface):
    interface = validate_interface(interface)
    output = subprocess.check_output(["ifconfig", interface], text=True)
    if output:
        ip_regex = r"(?:inet) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
        ip_groups = re.findall(ip_regex, output)
        if len(ip_groups) == 1:
            ip = ip_groups[0]
            return ip

    raise Exception(f"IP not found for {interface}")


def is_current_mac_same_as_stored(interface):
    return get_current_mac(interface) == get_stored_mac(interface)


def _send_sudo_command(command, password):
    child = pexpect.spawn(command)
    child.expect("Password:")
    child.sendline(password)
    status = child.expect(pexpect.EOF)
    return status


def reset_mac(interface: str):
    change_mac_unix(interface, ORIGINAL_MAC_ADDRESSES[interface])


def change_mac_unix(interface, new_mac):
    print("[+] Changing Mac Address for ", interface, "to ", new_mac)

    down_command = f"sudo networksetup -setairportpower {interface} off"
    up_command = f"sudo networksetup -setairportpower {interface} on"
    change_mac_command = f"sudo ifconfig {interface} ether {new_mac}"
    detect_hardware_command = "sudo networksetup -detectnewhardware"

    status = _send_sudo_command(down_command, password)
    status = _send_sudo_command(up_command, password)
    status = _send_sudo_command(change_mac_command, password)
    status = _send_sudo_command(detect_hardware_command, password)
    return status


def get_arguments():
    parser = optparse.OptionParser()
    parser.add_option(
        "-i",
        "--interface",
        dest="interface",
        help="Interface to change its MAC Address",
    )
    parser.add_option(
        "-m", "--mac", dest="new_mac", help="Interface to change its MAC Address"
    )
    (option, arguments) = parser.parse_args()
    if not option.interface:
        parser.error("[-] Please specify an Interface , use --help for more info.")
    elif not option.new_mac:
        parser.error("[-] Please specify an Mac Address , use --help for more info.")
    return option


def get_current_mac(interface: str):
    ifconfig_result = subprocess.check_output(["ifconfig", interface])
    mac_address_search_reslut = re.search(
        r"\w\w:\w\w:\w\w:\w\w:\w\w:\w\w", str(ifconfig_result)
    )
    if mac_address_search_reslut:
        return mac_address_search_reslut.group(0)
    else:
        return "[-] No mac address found in this interface : " + str(interface)


def validate_mac(mac: str):
    mac = mac.lower().strip()
    mac_address_regex = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
    match = mac_address_regex.match(mac)
    if match:
        return mac
    else:
        raise Exception(f"{mac} is not valid")


def validate_interface(interface: str):
    interface = interface.strip().lower()
    validation = interface in ORIGINAL_MAC_ADDRESSES.keys()
    if validation:
        return interface
    else:
        raise Exception(
            f"Interface {interface} is not in the list of the available interfaces to be changed."
        )


def change_mac_random(interface: str):
    mac = generate_mac.total_random()

    change_mac(interface, mac)


def change_mac(interface: str, new_mac: str):
    validated_interface = validate_interface(interface)
    validated_mac = validate_mac(new_mac)

    if validated_mac:
        # The MAC address string is valid
        current_mac = get_current_mac(validated_interface)
        print("[+] Current Mac :" + current_mac)
        change_mac_unix(validated_interface, validated_mac)
        current_mac = get_current_mac(validated_interface)

        if current_mac == validated_mac:
            print("[+] Mac address was successfully changed to  :" + current_mac)
        else:
            print("[-] Mac address did not get changed .")
    else:
        # The MAC address string is invalid
        print("Invalid MAC address")


# def main():
#     # the_signature()
#     mac_address_regex = re.compile(r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")

#     options = get_arguments()

#     match = mac_address_regex.match(str(options.new_mac))

#     if match:
#         # The MAC address string is valid
#         current_mac = get_current_mac(options.interface)
#         print("[+] Current Mac :" + current_mac)
#         change_mac_unix(options.interface, options.new_mac)
#         current_mac = get_current_mac(options.interface)

#         if current_mac == options.new_mac.lower():
#             print("[+] Mac address was successfully changed to  :" + current_mac)
#         else:
#             print("[-] Mac address did not get changed .")
#     else:
#         # The MAC address string is invalid
#         print("Invalid MAC address")
