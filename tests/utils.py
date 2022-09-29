import time
import threading
import json

TIMEOUT = 10
TIMEOUT_LONG = 30

def wait_for_threads(num=1):
    """Return after the total number of threads is num."""
    for _ in range(TIMEOUT):
        if len(threading.enumerate()) == num:
            return
        time.sleep(1)
    raise Exception("Failed to close threads.")


def wait_for_right_messages(function, mock_socket, num=1):
    """Return when function() evaluates to True on num messages."""
    for _ in get_right_messages(function, mock_socket, num):
        pass


def get_right_messages(function, mock_socket, num=1):
    """Yield every 1s, return when function()==True on num messages."""
    for _ in range(TIMEOUT_LONG):
        messages = get_messages(mock_socket)
        n_true_messages = sum(function(m) for m in messages)
        if n_true_messages == num:
            return
        yield
        time.sleep(1)
    raise Exception(f"Expected {num} messages, got {n_true_messages}.")


def get_messages(mock_socket):
    """Return a list decoded JSON messages sent via mock_socket sendall()."""
    messages = []

    # Add sendall returns that do and do not use context managers
    args_list = \
        mock_socket.return_value.__enter__.return_value.sendall.call_args_list

    for args, _ in args_list:
        message_str = args[0].decode('utf-8')
        message_dict = json.loads(message_str)
        messages.append(message_dict)

    return messages
