# This is the python script that will interpret FMCW demodulated IQ data published via ZMQ Publisher for a radar system
# Written by Ben Cometto, 8 May 2025

import zmq
import sys
import time
import numpy as np
import matplotlib.pyplot as plt



# variables
socket_loc = "tcp://localhost:4444"

current_time = 0       # timing values for update period
last_time = 0
period_ms = 100

current_data = b""      # variables for data handling
current_complexes = []
new_complex = 0

samp_rate = int(200e6)
decimation = 1
fs = samp_rate/decimation    # Sampling frequency
N = 1024                     # FFT size
update_rate = 0.1  # seconds between updates
df = samp_rate/N

B = 2*190e6           # FMCW parameters
tchirp = 5e-6
c = 300e6
alpha = B/tchirp

x = 50                 # Kalman Filter values
p = 100
r = 5
z = 0

K = 1
xlast = x
plast = p

# Set up FFT plot
t = np.arange(N) / fs
fig, ax = plt.subplots()
line, = ax.plot([], [], lw=2)
ax.set_xlim(0, fs/2)
ax.set_ylim(-80, 10)

ax.set_title("Beat Frequency Data")
ax.set_xlabel("Frequency (Hz)")
ax.set_ylabel("Magnitude (dB)")
ax.grid(True)



#  Set up socket to talk to GNU Radio
context = zmq.Context()
sub_socket = context.socket(zmq.SUB)
sub_socket.setsockopt(zmq.SUBSCRIBE, b"")
sub_socket.setsockopt(zmq.CONFLATE, 1) 
sub_socket.connect(socket_loc)

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
        current_complexes += complex_array.tolist()

    

    # If there is enough complexes, update estimate
    while len(current_complexes) >= N:
        signal = np.array(current_complexes[:N])
        current_complexes = current_complexes[N:]

        fft_result = np.fft.fft(signal)
        freqs = np.fft.fftfreq(N, d=1/fs)
        magnitude = np.abs(fft_result[:N//2])

        max_mag = max(magnitude)

        magnitude_db = 20 * np.log10(magnitude/max_mag + 1e-12)
        
        
        # Update plot
        line.set_data(freqs[:N//2], magnitude_db)
        fig.canvas.draw()
        fig.canvas.flush_events()
        plt.pause(update_rate)

        # Kalman Filter for State Estimation
        # Dynamic Model: xn+1,n = xn,n
        # Estimate uncertainty: pn+1,n = pn,n
        # Kalman Gain: Kn = pn+1,n/(pn+1,n-rn)
        # Predict: xn+1,n+1 = xn+1,n+Kn*(zn-xn+1,n)
        # Update uncertainty: pn+1,n+1 = (1-Kn)*pn+1,n

        # Measure distance
        kbeat = np.argmax(magnitude_db)
        measured_distance = kbeat*df*c/2/alpha
        
        # State update
        K = plast/(plast+r)
        x = xlast + K*(measured_distance - xlast)
        p = (1-K)*plast

        # State Predict - not needed due to constant dynamics, just x = x and p = p

        # Reset for next round
        xlast = x
        plast = p

        print(f"Measurement: {measured_distance:06.2f} | State: {x:06.3f}")



        
        
        