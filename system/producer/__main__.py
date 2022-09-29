from email.policy import default
import random
import time
import socket
import json
import os
import logging
import threading
import sys
from system.utils import send_msg_tcp
import click
# Configure logging
LOGGER = logging.getLogger(__name__)

class Producer:
    def __init__(self, port, monitor_port, msg_num = 1000):
        """Construct a Producer instance and start listening for messages."""
        self.msg_num = msg_num
        self.available_senders = []
        self.senders = set()
        self.msg_queue = []
        self.shut_down = False
        self.port = port
        self.monitor_port = monitor_port
        self.status = {"num_sent": 0, "num_fail": 0, "total_time": 0}
        self.create_listen_thread()
        self.start_producer()

    def start_producer(self):
        """Generate all msgs and tell monitor to start monitoring."""
        self.generate_all_msgs()
        send_msg_tcp(self.monitor_port, {"message_type": "start"})
    
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
                    clientsocket, address = sock.accept()
                except socket.timeout:
                    continue

                with clientsocket:
                    message_chunks = []
                    while not self.shut_down:
                        try:
                            data = clientsocket.recv(4096)
                        except socket.timeout:
                            continue
                        if not data:
                            break
                        message_chunks.append(data)

                message_bytes = b''.join(message_chunks)
                message_str = message_bytes.decode("utf-8")
                try:
                    message_dict = json.loads(message_str)
                except json.JSONDecodeError:
                    continue

                if message_dict["message_type"] == "register":
                    self.handle_sender_registration(message_dict)
                elif message_dict["message_type"] == "finished":
                    self.handle_send_finished(message_dict)
                elif message_dict["message_type"] == "status":
                    self.handle_status_update()
                elif message_dict["message_type"] == "shutdown":
                    self.handle_shutdown()

    def handle_sender_registration(self, register_info):
        """Handle the Sender registration. Assign msgs to Sender if having msgs in queue."""
        sender_port = register_info["sender_port"]
        self.available_senders.append(sender_port)
        self.senders.add(sender_port)
        self.assign_messages()    

    def handle_send_finished(self, finish_info):
        """Handle the Sender finish. Collect the statistics and assgin new msg to the Sender."""
        success, send_time = finish_info["success"], finish_info["send_time"]
        sender_port = finish_info["sender_port"]
        if not success:
            self.status["num_fail"] += 1
        else:
            self.status["num_sent"] += 1
            self.status["total_time"] += send_time

        self.available_senders.append(sender_port)
        self.assign_messages() 

    def handle_status_update(self):
        """Handle the Monitor request. Send back the current status."""
        update_msg = {"message_type": "status"}
        update_msg.update(self.status)
        send_msg_tcp(self.monitor_port, update_msg)
        
    def handle_shutdown(self):
        """Handle the User shutdown. Send shutdown requests to Senders and Monitor."""
        for sender_port in self.senders:
            shutdown_msg = {"message_type": "shutdown"}
            send_msg_tcp(sender_port, shutdown_msg)
        send_msg_tcp(self.monitor_port, shutdown_msg)
        # wait for monitor and senders shutdown
        time.sleep(1)
        self.shut_down= True

    def assign_messages(self):
        """Assign msg to available sender."""
        while self.available_senders and self.msg_queue:
            sender_port = self.available_senders.pop(0)
            msg_id, phone, msg = self.msg_queue.pop(0)
            task = {
                "message_type": "sendmsg",
                "msg_id": msg_id,
                "phone": phone,
                "msg": msg
            }
            send_msg_tcp(sender_port, task)

    def generate_phone_number(self):
        """Generate a valid phone number."""
        phoneNumber = ""
        for _ in range(9):
            phoneNumber += str(random.randint(0, 9))
        return phoneNumber

    def generate_single_msg(self):
        """Generate a valid msg."""
        msg_len = random.randint(1, 100)
        msg = ""
        for _ in range(msg_len):
            msg += chr(random.randint(0, 25)+ord('a'))
        return msg
    
    def generate_all_msgs(self):
        """Generate all msgs at once."""
        for msg_id in range(self.msg_num):
            self.msg_queue.append((msg_id, self.generate_phone_number(), self.generate_single_msg()))
   

@click.command()
@click.option("--port", "port", default=6000)
@click.option("--monitor-port", "monitor_port", default=5999)
@click.option("--msg-num", "msg_num", default=1000)
def main(port, monitor_port, msg_num):
    """Run Producer."""
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        f"Producer:{port} [%(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    Producer(port, monitor_port, msg_num)


if __name__ == '__main__':
    main()