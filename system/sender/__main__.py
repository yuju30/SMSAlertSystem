import random
import socket
import json
import logging
import time
import threading
import click
import sys
from system.utils import send_msg_tcp

LOGGER = logging.getLogger(__name__)

class Sender:
    def __init__(self, port, producer_port, mean_time, failure_rate):
        """Construct a Sender instance and start listening for messages."""
        self.mean_time = mean_time
        self.failure_rate = failure_rate
        self.port = port
        self.producer_port = producer_port
        self.shut_down = False
        self.create_listen_thread()
        self.start_sender()
    
    def start_sender(self):
        """Send registration msgs to Producer along with my port."""
        register_msg = {
            "message_type": "register",
            "sender_port": self.port
        }
        send_msg_tcp(self.producer_port, register_msg)

    def create_listen_thread(self):
        """Create thread running for listening msgs."""
        listen_thread = threading.Thread(target=self.listen_on_tcp)
        listen_thread.start()

    def listen_on_tcp(self):
        """Set up TCP Socket Server to listen for msgs."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Bind the socket to the server
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("localhost", self.port))
            sock.listen()

            sock.settimeout(1)
            while not self.shut_down:

                try:
                    producersocket, _ = sock.accept()
                except socket.timeout:
                    continue

                with producersocket:
                    msg_chunks = []
                    while not self.shut_down:
                        try:
                            data = producersocket.recv(4096)
                        except socket.timeout:
                            continue
                        if not data:
                            break
                        msg_chunks.append(data)
                # Decode list-of-byte-strings to UTF8 and parse JSON data
                msg_bytes = b''.join(msg_chunks)
                msg_str = msg_bytes.decode("utf-8")
                try:
                    msg_dict = json.loads(msg_str)
                except json.JSONDecodeError:
                    continue

                if msg_dict["message_type"] == "sendmsg":
                    self.handle_msg_send(msg_dict)
                elif msg_dict["message_type"] == "shutdown":
                    self.handle_shutdown()

    def handle_msg_send(self, msg_info):
        """Handle Producer request to send msgs."""
        wait_time = random.gauss(self.mean_time, 1)
        time.sleep(wait_time)
        success = self.send_success()
        send_result = {
            "message_type": "finished",
            "sender_port": self.port,
            "success": success,
            "send_time": wait_time
        }
        if success:
            LOGGER.info("Send {%s} --> phone number: %s", msg_info["msg"], msg_info["phone"])

        if not self.shut_down:
            send_msg_tcp(self.producer_port, send_result)        

    def handle_shutdown(self):
        """Handle Producer request to shutdown."""
        self.shut_down = True

    def send_success(self):
        """Calculate the success rate."""
        return random.random() > self.failure_rate



@click.command()
@click.option("--port", "port", default=6001)
@click.option("--producer-port", "producer_port", default=6000)
@click.option("--mean-time", "mean_time", default=10)
@click.option("--failure-rate", "failure_rate", default=0.2)
def main(port, producer_port, mean_time, failure_rate):
    """Run Sender."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        f"Sender:{port} [%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    Sender(port, producer_port, mean_time, failure_rate)


if __name__ == '__main__':
    main()