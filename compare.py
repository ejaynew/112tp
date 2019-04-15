import pyaudio
import sys
import numpy as np
import aubio

import sys
import subprocess
import cv2
import time
import numpy as np
from SheetVision.best_fit import fit
from SheetVision.rectangle import Rectangle
from SheetVision.note import Note
from random import randint
from SheetVision.midiutil.MidiFile3 import MIDIFile

from detectPitches import recordPitchFromInput
from SheetVision.main import jpg2midi

jpg2midi("/Users/emma/Documents/15-112/TP/SheetVision/resources/samples/fire.jpg")