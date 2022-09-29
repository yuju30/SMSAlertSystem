import socket
import json

def send_msg_tcp(port, msg_dict):
    """Set up TCP Socket Client and send msgs."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        # connect to the server
        sock.connect(("localhost", port))
        # send a message
        message = json.dumps(msg_dict)
        sock.sendall(message.encode('utf-8'))
