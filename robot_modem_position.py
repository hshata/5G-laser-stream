### 5G Modem ####
## DATA1 10.45.1.5  netmask 255.255.0.0 ##
## wwp0s20u3i5 192.168.2.2  netmask 255.255.255.0 ##

import zmq, threading, time
import YRC_2

robo = YRC_2.motoman()
latest_pose = None

def poll_pose():
    global latest_pose
    while True:
        try:
            latest_pose = robo.get_pose()
        except:
            latest_pose = None
        time.sleep(0.1)  # 10 Hz polling

threading.Thread(target=poll_pose, daemon=True).start()

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://192.168.2.2:5560")

print("[ROBOT-MODEM] Ready")

while True:
    msg = socket.recv_string()
    if msg == "GET_POS":
        if latest_pose:
            socket.send_pyobj({"status": "ok", "position": latest_pose})
        else:
            socket.send_pyobj({"status": "error", "message": "No data yet"})
