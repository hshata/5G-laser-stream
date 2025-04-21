import zmq
import time

###5G Base Station (192.168.2.1, tun0) with 5G Modem (192.168.2.2, wwp0s20u3i5)
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://192.168.2.2:5556")
socket.setsockopt_string(zmq.SUBSCRIBE, '')

###PUSH socket to forward the received data to the edge server
push_socket = context.socket(zmq.PUSH)
push_socket.connect("tcp://10.46.2.3:9999")  #edge server's IP address and port number

print("[SUB] Waiting for data...")

while True:
    payload = socket.recv_pyobj()
    recv_time = time.time()

    sent_time = payload["timestamp"]
    latency = (recv_time - sent_time) * 1000

    data = payload["data"]
    print(f"[SUB] Received data with shape: {data.shape}")
    print(f"[LATENCY] {latency:.2f} ms")


    ###Forward the payload message to the edge server via the PUSH socket
    push_socket.send_pyobj(payload)
    print(f"[BASE STATION] Forwarded data to the edge server at 10.46.2.3:9999")
