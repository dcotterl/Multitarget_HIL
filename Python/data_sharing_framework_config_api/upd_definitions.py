import socket
import struct


def ip_to_int_string(ip_address: str) -> str:
    """Convert an IPv4 address string (e.g. '127.0.0.1') into its integer
    representation as a string (e.g. '2130706433')."""
    packed = socket.inet_aton(ip_address)
    return str(struct.unpack("!L", packed)[0])


def int_string_to_ip(int_string: str) -> str:
    """Convert an integer string (e.g. '2130706433') back into its IPv4
    address representation (e.g. '127.0.0.1')."""
    packed = struct.pack("!L", int(int_string))
    return socket.inet_ntoa(packed)


if __name__ == "__main__":
    # Example usage
    ip = "127.0.0.2"
    int_str = ip_to_int_string(ip)
    print(f"IP address {ip} as integer string: {int_str}")
    ip_converted_back = int_string_to_ip(int_str)
    print(f"Integer string {int_str} converted back to IP address: {ip_converted_back}")