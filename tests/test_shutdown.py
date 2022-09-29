import json
import system
import utils


TIMEOUT = 10

def test_sender_shutdown(mocker):
    """Test sender successfully shutdown given shutdown requests."""
    mock_socket = mocker.patch('socket.socket')
    mocksendersocket = mocker.MagicMock()
    mocksendersocket.recv.side_effect = [
        json.dumps({"message_type": "shutdown"}).encode('utf-8'),
        None,
    ]

    mock_socket.return_value.__enter__.return_value.accept.return_value = (
        mocksendersocket,
        ("localhost", 10000),
    )

    try:
        system.Sender(
            port=3001, 
            producer_port=6000, 
            mean_time=5, 
            failure_rate=0.2
        )
        utils.wait_for_threads()
    except SystemExit as error:
        assert error.code == 0


def test_producer_shutdown(mocker):
    """Test producer and sender successfully shutdown given producer shutdown requests."""
    mock_socket = mocker.patch('socket.socket')
    mockproducersocket = mocker.MagicMock()
    mockproducersocket.recv.side_effect = [
        # First fake sender registers with producer
        json.dumps({
            "message_type": "register",
            "sender_port": 3001,
        }).encode('utf-8'),
        None,
        # Second fake sender registers with producer
        json.dumps({
            "message_type": "register",
            "sender_port": 3002,
        }).encode('utf-8'),
        None,
        # Fake shutdown message sent to producer
        json.dumps({
            "message_type": "shutdown",
        }).encode('utf-8'),
        None,
    ]

    mock_socket.return_value.__enter__.return_value.accept.return_value = (
        mockproducersocket,
        ("localhost", 10000),
    )

    try:
        system.Producer(port=6000, monitor_port=5999)
        utils.wait_for_threads()
    except SystemExit as error:
        assert error.code == 0

