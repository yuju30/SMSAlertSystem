import json
import system
import utils

def generate_sender_message(mock_socket):
    """Generate msgs for sender and wait for response."""
    # send sender msg request
    yield json.dumps({
        "message_type": "sendmsg",
        "msg_id": 0,
        "phone": "123456789",
        "msg": "abc"
    }).encode('utf-8')
    yield None

    # wait for finished msgs 
    utils.wait_for_right_messages(is_finished, mock_socket)

    # shutdown
    yield json.dumps({
        "message_type": "shutdown",
    }).encode('utf-8')
    yield None

def test_sender_send(mocker):
    """Test sender successfully send msgs given msg sending requests."""
    mocksendersocket = mocker.MagicMock()
    mock_socket = mocker.patch('socket.socket')
    mock_socket.return_value.__enter__.return_value.accept.return_value = (
        mocksendersocket,
        ("localhost", 10000),
    )
    
    mocksendersocket.recv.side_effect = generate_sender_message(mock_socket)
    try:
        system.Sender(
            port=6001,
            producer_port=6000,
            mean_time=1,
            failure_rate=0.0
        )
        utils.wait_for_threads()
    except SystemExit as error:
        assert error.code == 0

def is_finished(message):
    """Test message type is finished msg."""
    return ("message_type" in message and
        message["message_type"] == "finished")

