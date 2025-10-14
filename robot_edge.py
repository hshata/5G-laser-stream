import zmq

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://10.46.2.2:5561")  # Base station IP

print("[EDGE] Requesting robot position...")
socket.send_string("GET_POS")

reply = socket.recv_pyobj()
print(f"[EDGE] Received robot position: {reply}")
