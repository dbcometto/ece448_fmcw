# This is the python script that will interpret FMCW demodulated IQ data published via 2x ZMQ Push for a radar system
# Written by Ben Cometto, 8 May 2025

import zmq
import sys
import time
import numpy as np




# variables
socket_loc = "tcp://localhost:4444"

current_time = 0
last_time = 0
period_ms = 100

current_data = b""
current_complexes = []
new_complex = 0



#  Set up socket to talk to GNU Radio
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)
sub_socket.connect(socket_loc)
sub_socket.setsockopt(zmq.SUBSCRIBE, b"")

print(f" I am setup and waiting for messages on {socket_loc}")


# Main Processing Loop
while True: 

    # get new data every once in a while
    current_time = time.time()*1000
    if (current_time-last_time) > period_ms:
        # Get new data
        try:
            current_data += sub_socket.recv() # concactenate new data onto old data
        except:
            pass   

        last_time = current_time 

    # If there is enough data, get a new complex value    
    while len(current_data) >= 16: 
        # pull int out of byte data
        num_complex = len(current_data) // 8

        complex_array = np.frombuffer(current_data[:num_complex*8], dtype=np.complex64) #int.from_bytes(current_data[0]) 
        current_data = current_data[num_complex*8:] # delete data off of the front of the queue
        current_complexes.append(complex_array.tolist())

        # current state and next state logic

    # If there is enough complexes, print
    while len(current_complexes) >= 2:
        print(current_complexes[0:2])
        current_complexes = []
        