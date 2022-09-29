import system
import utils
import json

def generate_monitor_message(mock_socket):
    """Generate msgs for monitor and wait for response."""
    # ask the monitor to start
    yield json.dumps({
        "message_type": "start",
    }).encode('utf-8')
    yield None

    # wait for update request 
    utils.wait_for_right_messages(is_status_update, mock_socket)

    # shutdown
    yield json.dumps({
        "message_type": "shutdown",
    }).encode('utf-8')
    yield None

def test_monitor_start(mocker):
    """Test monitor start monitoring after getting start msg from producer."""
    mockmonitorsocket = mocker.MagicMock()
    mock_socket = mocker.patch('socket.socket')
    mock_socket.return_value.__enter__.return_value.accept.return_value = (
        mockmonitorsocket,
        ("localhost", 10000),
    )
    
    mockmonitorsocket.recv.side_effect = generate_monitor_message(mock_socket)
    try:
        system.Monitor(
            port=5999,
            producer_port=6000,
            N = 1,
        )
        utils.wait_for_threads()
    except SystemExit as error:
        assert error.code == 0

def is_status_update(message):
    """Test message type is status update request."""
    return ("message_type" in message and
        message["message_type"] == "status")