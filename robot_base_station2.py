import zmq

context = zmq.Context()

###Listen for edge requests
frontend = context.socket(zmq.REP)
frontend.bind("tcp://10.46.2.2:5561")  # Base station DATA2 IP

###connect to modem
backend = context.socket(zmq.REQ)
backend.connect("tcp://192.168.2.2:5560")  # Modem 5G IP

print("[BASE-STATION] Ready to relay robot position requests")

while True:
    msg = frontend.recv_string()
    print(f"[BASE-STATION] Received from edge: {msg}")

    backend.send_string(msg)
    reply = backend.recv_pyobj()

    frontend.send_pyobj(reply)
