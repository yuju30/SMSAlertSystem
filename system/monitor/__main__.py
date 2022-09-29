import socket
import json
import logging
import time
import threading
import sys
import click

from system.utils import send_msg_tcp

LOGGER = logging.getLogger(__name__)

class Monitor:
    def __init__(self, port, producer_port, N):
        """Construct a Monitor instance and start listening for messages."""
        self.monitor_interval = N
        self.port = port
        self.producer_port = producer_port
        self.shut_down = False
        self.query_thread = threading.Thread(target=self.query_update)
        self.create_listen_thread()

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

                if msg_dict["message_type"] == "status":
                    self.handle_update(msg_dict)
                elif msg_dict["message_type"] == "start":
                    self.query_thread.start()
                elif msg_dict["message_type"] == "shutdown":
                    self.handle_shutdown()

    def query_update(self):
        """Query the Producer every N secs for the updated status."""
        while not self.shut_down:
            update_msg = {"message_type": "status"}
            send_msg_tcp(self.producer_port, update_msg)
            time.sleep(self.monitor_interval)

    def handle_update(self, update_info):
        """Display the result of updated status from the Producer."""
        num_sent, num_fail = update_info["num_sent"], update_info["num_fail"]
        if update_info["num_sent"] == 0:
            avg_time = 0
        else:
            avg_time = update_info["total_time"] // update_info["num_sent"]
        
        LOGGER.info("===========================================")
        LOGGER.info("Number of messages sent : {}".format(num_sent))
        LOGGER.info("Number of messages failed : {}".format(num_fail))
        LOGGER.info("Average time per message : {}".format(avg_time))
        LOGGER.info("===========================================")

    def handle_shutdown(self):
        """Handle Producer request to shutdown."""
        self.shut_down = True

    
@click.command()
@click.option("--port", "port", default=5999)
@click.option("--producer-port", "producer_port", default=6000)
@click.option("--N", "N", default=15)
def main(port, producer_port, N):
    """Run Monitor."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        f"Monitor:{port} [%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    Monitor(port, producer_port, N)


if __name__ == '__main__':
    main()