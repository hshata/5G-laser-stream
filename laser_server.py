# ==============================================================================
# Project Name: point-cloud
# Author: Hussein Shata (hshata) [ElHussein Shata]
# GitHub: https://github.com/hshata/5G-laser-stream.git
# Description: This repository streams data from gocator sensor in real-time over 5G link
#
# "Code is like humor. When you have to explain it, it’s bad." – Cory House
# ==============================================================================


import os
import ctypes
import numpy as np
import zmq
import time

from ctypes import *
from laserScanner import MsgManager


#Linux
kApi = ctypes.cdll.LoadLibrary(os.path.join('/home/native/Desktop/Hussein/GO_SDK/', 'lib', 'linux_x64d', 'libkApi.so'))
GoSdk = ctypes.cdll.LoadLibrary(os.path.join('/home/native/Desktop/Hussein/GO_SDK/', 'lib', 'linux_x64d', 'libGoSdk.so'))

### Sensor Constants
ip_address = b"10.45.3.1"
RECEIVE_TIMEOUT = 10000

### Type Aliases
kObject = ctypes.c_void_p
kValue = ctypes.c_uint32
kSize = ctypes.c_ulonglong
kAssembly = ctypes.c_void_p
GoSystem = ctypes.c_void_p
GoSensor = ctypes.c_void_p
GoDataSet = ctypes.c_void_p
GoDataMsg = ctypes.c_void_p

### Constants
GO_DATA_MESSAGE_TYPE_UNIFORM_PROFILE = 7
kNULL = 0
kTRUE = 1
kFALSE = 0

### Structs
class GoStampData(Structure):
    _fields_ = [("frameIndex", c_uint64), ("timestamp",c_uint64), ("encoder", c_int64), ("encoderAtZ", c_int64), ("status", c_uint64), ("id", c_uint32)]

class kIpAddress(Structure):
    _fields_ = [("kIpVersion", c_int32),("kByte",c_char*16)]

GoSdk.GoDataSet_At_argtypes = [kObject, kSize]
GoSdk.GoDataSet_At.restype = kObject
GoSdk.GoDataMsg_Type.argtypes = [kObject]
GoSdk.GoDataMsg_Type.restype = kValue
GoSdk.GoResampledProfileMsg_At.restype = ctypes.POINTER(ctypes.c_short)

### ZMQ publisher
context = zmq.Context()
pub_socket = context.socket(zmq.PUB)
pub_socket.bind("tcp://192.168.2.2:5556")
print("[ZMQ] Publisher ready at tcp://*:5556")

### Helper
def kObject_Destroy(obj):
    if obj and obj != kNULL:
        kApi.xkObject_DestroyImpl(obj, kFALSE)

### Main data handler
def RecieveData(dataset):
    for i in range(GoSdk.GoDataSet_Count(dataset)):
        dataObj = GoDataMsg(GoSdk.GoDataSet_At(dataset, i))
        
        if GoSdk.GoDataMsg_Type(dataObj) == GO_DATA_MESSAGE_TYPE_UNIFORM_PROFILE:
            profileMsg = dataObj

            for k in range(GoSdk.GoResampledProfileMsg_Count(profileMsg)):
                XResolution = GoSdk.GoResampledProfileMsg_XResolution(profileMsg) / 1e6
                ZResolution = GoSdk.GoResampledProfileMsg_ZResolution(profileMsg) / 1e6
                XOffset = GoSdk.GoResampledProfileMsg_XOffset(profileMsg) / 1e3
                ZOffset = GoSdk.GoResampledProfileMsg_ZOffset(profileMsg) / 1e3
                width = GoSdk.GoProfileMsg_Width(profileMsg)

                profileDataPtr = GoSdk.GoResampledProfileMsg_At(profileMsg, k)
                Z = np.ctypeslib.as_array(profileDataPtr, shape=(width,))
                Z = Z.astype(np.double)
                Z[Z == -32768] = np.nan
                Z = Z * ZResolution + ZOffset

                X = np.arange(width, dtype=np.double) * XResolution + XOffset
                data = np.stack((X, Z), axis=1)  # Shape: (N, 2)

                timestamp = int(time.time())
                data_transposed = data.T
                new_data = np.insert(data_transposed, 0, timestamp, axis=1)

                # ZMQ publish
##                pub_socket.send_pyobj(new_data)
##                print(f"[ZMQ] Published scan with shape: {new_data.shape}")

                timedelay = time.time()
                payload = {
                    "timestamp": timedelay,
                    "data": new_data
                    }
                pub_socket.send_pyobj(payload)
                print(payload)
                

    kObject_Destroy(dataset)

### Sensor setup + scanning
def start_sensor():
    api = kAssembly(kNULL)
    system = GoSystem(kNULL)
    sensor = GoSensor(kNULL)

    GoSdk.GoSdk_Construct(byref(api))
    GoSdk.GoSystem_Construct(byref(system), kNULL)

    ipAddr_ref = kIpAddress()
    kApi.kIpAddress_Parse(byref(ipAddr_ref), ip_address)
    GoSdk.GoSystem_FindSensorByIpAddress(system, byref(ipAddr_ref), byref(sensor))

    GoSdk.GoSensor_Connect(sensor)
    GoSdk.GoSystem_EnableData(system, kTRUE)

    print("[Sensor] Connected.")

    mgr = MsgManager(GoSdk, system, GoDataSet(kNULL))
    mgr.SetDataHandler(RECEIVE_TIMEOUT, RecieveData)

    GoSdk.GoSensor_Stop(sensor)
    GoSdk.GoSensor_Start(sensor)
    print("[Sensor] Started.")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("[Sensor] Shutting down.")
    finally:
        kObject_Destroy(system)
        kObject_Destroy(api)
        pub_socket.close()
        context.term()

### Main Entry
if __name__ == "__main__":
    print("[Main] Launching laser scanner with ZMQ integration.")
    start_sensor()
