##### ADAPTED FROM https://github.com/aubio/aubio/blob/master/python/demos/demo_pyaudio.py

#! /usr/bin/env python

# Use pyaudio to open the microphone and run aubio.pitch on the stream of
# incoming samples. If a filename is given as the first argument, it will
# record 5 seconds of audio to this location. Otherwise, the script will
# run until Ctrl+C is pressed.

# Examples:
#    $ ./python/demos/demo_pyaudio.py
#    $ ./python/demos/demo_pyaudio.py /tmp/recording.wav

class Pitch(object):
    def __init__(self, pitch, confidence):
        self.pitch = pitch
        self.confidence = confidence
    def __repr__(self):
        return "%s / %s" % (self.pitch, self.confidence)
        
def getAverage(lst):
    return sum(lst) / len(lst)

def recordPitchFromInput(duration):
    import pyaudio
    import sys
    import numpy as np
    import aubio
    
    pitches = []
    
    # initialise pyaudio
    p = pyaudio.PyAudio()
    
    # open stream
    buffer_size = 1024
    pyaudio_format = pyaudio.paFloat32
    n_channels = 1
    samplerate = 12000 #44100
    stream = p.open(format=pyaudio_format,
                    channels=n_channels,
                    rate=samplerate,
                    input=True,
                    frames_per_buffer=buffer_size)
    
    outputsink = None
    total_frames = 0
    record_duration = duration - 0.85 # number determined through trial/error
    
    # setup pitch
    tolerance = 0.8
    win_s = 4096 # fft size
    hop_s = buffer_size # hop size
    pitch_o = aubio.pitch("default", win_s, hop_s, samplerate)
    pitch_o.set_unit("midi")
    pitch_o.set_tolerance(tolerance)
    
    print("*** starting recording")
    while True:
        try:
            audiobuffer = stream.read(buffer_size)
            signal = np.fromstring(audiobuffer, dtype=np.float32)
    
            pitch = pitch_o(signal)[0]
            confidence = pitch_o.get_confidence()
            
            pitches.append(pitch)
    
            print("{} / {}".format(pitch,confidence))
    
            if outputsink:
                outputsink(signal, len(signal))
    
            if record_duration:
                total_frames += len(signal)
                if record_duration * samplerate < total_frames:
                    break
                    
        except KeyboardInterrupt:
            print("*** Ctrl+C pressed, exiting")
            break
    
    print("*** done recording")
    stream.stop_stream()
    stream.close()
    p.terminate()
    return getAverage(pitches)
    
# import time
# t1 = time.time()
# recordPitchFromInput(.2)
# t2 = time.time()
# print(t2 - t1)

print(recordPitchFromInput(2))