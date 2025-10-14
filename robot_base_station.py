import zmq

context = zmq.Context()
frontend = context.socket(zmq.REP)
frontend.bind("tcp://10.46.2.3:5561")  #Edge sends

#Backend: to Robot Modem
backend = context.socket(zmq.REQ)
backend.connect("tcp://192.168.2.2:5560")  #Connect to modem's REP

print("[BASE-STATION] Proxy active between Edge <-> Robot Modem")

while True:
    ###1.Receive command from edge
    msg = frontend.recv_string()
    print(f"[BASE-STATION] Received command from edge: {msg}")

    ###2. Forward to robot modem
    backend.send_string(msg)

    ###3. Wait for reply from robot modem
    reply = backend.recv_pyobj()
    print(f"[BASE-STATION] Got reply from robot modem: {reply}")

    ###4. Send back to edge
    frontend.send_pyobj(reply)
