import cv2
import math

class Rectangle(object):
    def __init__(self, x, y, w, h):
        self.x = x;
        self.y = y;
        self.w = w;
        self.h = h;
        self.middle = self.x + self.w/2, self.y + self.h/2
        self.area = self.w * self.h

    def overlap(self, other):
        overlap_x = max(0, min(self.x + self.w, other.x + other.w) - max(self.x, other.x));
        overlap_y = max(0, min(self.y + self.h, other.y + other.h) - max(self.y, other.y));
        overlap_area = overlap_x * overlap_y
        return overlap_area / self.area

    def distance(self, other):
        dx = self.middle[0] - other.middle[0]
        dy = self.middle[1] - other.middle[1]
        return math.sqrt(dx*dx + dy*dy)

    def merge(self, other):
        x = min(self.x, other.x)
        y = min(self.y, other.y)
        w = max(self.x + self.w, other.x + other.w) - x
        h = max(self.y + self.h, other.y + other.h) - y
        return Rectangle(x, y, w, h)

    def draw(self, img, color, thickness):
        pos = ((int)(self.x), (int)(self.y))
        size = ((int)(self.x + self.w), (int)(self.y + self.h))
        cv2.rectangle(img, pos, size, color, thickness)
        
note_step = 0.0625

note_defs = {
     -4 : ("g5", 79),
     -3 : ("f5", 77),
     -2 : ("e5", 76),
     -1 : ("d5", 74),
      0 : ("c5", 72),
      1 : ("b4", 71),
      2 : ("a4", 69),
      3 : ("g4", 67),
      4 : ("f4", 65),
      5 : ("e4", 64),
      6 : ("d4", 62),
      7 : ("c4", 60),
      8 : ("b3", 59),
      9 : ("a3", 57),
     10 : ("g3", 55),
     11 : ("f3", 53),
     12 : ("e3", 52),
     13 : ("d3", 50),
     14 : ("c3", 48),
     15 : ("b2", 47),
     16 : ("a2", 45),
     17 : ("f2", 53),
}

class Note(object):
    def __init__(self, rec, sym, staff_rec, sharp_notes = [], flat_notes = []):
        self.rec = rec
        self.sym = sym

        middle = rec.y + (rec.h / 2.0)
        height = (middle - staff_rec.y) / staff_rec.h
        note_def = note_defs[int(height/note_step + 0.5)]
        self.note = note_def[0]
        self.pitch = note_def[1]
        if any(n for n in sharp_notes if n.note[0] == self.note[0]):
            self.note += "#"
            self.pitch += 1
        if any(n for n in flat_notes if n.note[0] == self.note[0]):
            self.note += "b"
            self.pitch -= 1
            
import cv2
import matplotlib.pyplot as plt
import numpy as np

def fit(img, templates, start_percent, stop_percent, threshold):
    img_width, img_height = img.shape[::-1]
    best_location_count = -1
    best_locations = []
    best_scale = 1

    plt.axis([0, 2, 0, 1])
    plt.show(block=False)

    x = []
    y = []
    for scale in [i/100.0 for i in range(start_percent, stop_percent + 1, 3)]:
        locations = []
        location_count = 0
        for template in templates:
            template = cv2.resize(template, None,
                fx = scale, fy = scale, interpolation = cv2.INTER_CUBIC)
            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            result = np.where(result >= threshold)
            location_count += len(result[0])
            locations += [result]
        print("scale: {0}, hits: {1}".format(scale, location_count))
        x.append(location_count)
        y.append(scale)
        plt.plot(y, x)
        plt.pause(0.00001)
        if (location_count > best_location_count):
            best_location_count = location_count
            best_locations = locations
            best_scale = scale
            plt.axis([0, 2, 0, best_location_count])
        elif (location_count < best_location_count):
            pass
    plt.close()

    return best_locations, best_scale
    
#-----------------------------------------------------------------------------
# Name:        MidiFile.py
# Purpose:     MIDI file manipulation utilities
#
# Author:      Mark Conway Wirt <emergentmusics) at (gmail . com>
#
# Created:     2008/04/17
# Copyright:   (c) 2009 Mark Conway Wirt
# License:     Please see License.txt for the terms under which this
#              software is distributed.
#-----------------------------------------------------------------------------

import struct,  sys,  math

# TICKSPERBEAT is the number of "ticks" (time measurement in the MIDI file) that
# corresponds to one beat. This number is somewhat arbitrary, but should be chosen
# to provide adequate temporal resolution.

TICKSPERBEAT = 960

controllerEventTypes = {
                        'pan' : 0x0a
                        }
class MIDIEvent:
    '''
    The class to contain the MIDI Event (placed on MIDIEventList.
    '''
    def __init__(self):
        self.type='unknown'
        self.time=0
        self.ord = 0
        
    def __lt__(self, other):
        ''' Sorting function for events.'''
        if self.time < other.time:
            return True
        elif self.time > other.time:
            return False
        else:
            if self.ord < other.ord:
                return True
            elif self.ord > other.ord:
                return False
            else:
                return False

    def __cmp__(self, other):
        ''' Sorting function for events.'''
        if self.time < other.time:
            return -1
        elif self.time > other.time:
            return 1
        else:
            if self.ord < other.ord:
                return -1
            elif self.ord > other.ord:
                return 1
            else:
                return 0

class GenericEvent():
    '''The event class from which specific events are derived
    '''
    def __init__(self,time):
        self.time = time 
        self.type = 'Unknown'


        
    def __eq__(self, other):
        '''
        Equality operator for Generic Events and derived classes.
        
        In the processing of the event list, we have need to remove duplicates. To do this
        we rely on the fact that the classes are hashable, and must therefore have an 
        equality operator (__hash__() and __eq__() must both be defined).
        
        This is the most embarrassing portion of the code, and anyone who knows about OO
        programming would find this almost unbelievable. Here we have a base class that
        knows specifics about derived classes, thus breaking the very spirit of 
        OO programming.
        
        I suppose I should go back and restructure the code, perhaps removing the derived
        classes altogether. At some point perhaps I will.
        '''
        if self.time != other.time or self.type != other.type:
            return False
            
        # What follows is code that encodes the concept of equality for each derived 
        # class. Believe it f you dare.
        
        if self.type == 'note':
            if self.pitch != other.pitch or self.channel != other.channel:
                return False
        if self.type == 'tempo':
            if self.tempo != other.tempo:
                return False
        if self.type == 'programChange':
            if self.programNumber != other.programNumber or self.channel != other.channel:
                return False
        if self.type == 'trackName':
            if self.trackName != other.trackName:
                return False
        if self.type == 'controllerEvent':
            if self.parameter1 != other.parameter1 or \
                self.channel != other.channel or \
                self.eventType != other.eventType:
                return False
                
        if self.type == 'SysEx':
            if self.manID != other.manID:
                return False
                
        if self.type == 'UniversalSysEx':
            if self.code != other.code or\
                self.subcode != other.subcode or \
                self.sysExChannel != other.sysExChannel:
                return False
                
        return True
        
    def __hash__(self):
        '''
        Return a hash code for the object.
        
        This is needed for the removal of duplicate objects from the event list. The only
        real requirement for the algorithm is that the hash of equal objects must be equal.
        There is probably great opportunity for improvements in the hashing function.
        '''
        # Robert Jenkin's 32 bit hash.
        a = int(self.time)
        a = (a+0x7ed55d16) + (a<<12)
        a = (a^0xc761c23c) ^ (a>>19)
        a = (a+0x165667b1) + (a<<5)
        a = (a+0xd3a2646c) ^ (a<<9)
        a = (a+0xfd7046c5) + (a<<3)
        a = (a^0xb55a4f09) ^ (a>>16)
        return a

class MIDITrack:
    '''A class that encapsulates a MIDI track
    '''
    # Nested class definitions.
    
    class note(GenericEvent):
        '''A class that encapsulates a note
        '''
        def __init__(self,channel, pitch,time,duration,volume,annotation=None):
            
            GenericEvent.__init__(self,time)
            self.pitch = pitch
            self.duration = duration
            self.volume = volume
            self.type = 'note'
            self.channel = channel
            self.annotation = annotation
            
        def compare(self, other):
            '''Compare two notes for equality.
            '''
            if self.pitch == other.pitch and \
                self.time == other.time and \
                self.duration == other.duration and \
                self.volume == other.volume and \
                self.type == other.type and \
                self.channel == other.channel:
                    return True
            else:
                    return False
                    
            
    class tempo(GenericEvent):
        '''A class that encapsulates a tempo meta-event
        '''
        def __init__(self,time,tempo):
            
            GenericEvent.__init__(self,time)
            self.type = 'tempo'
            self.tempo = int(60000000 / tempo)
            
    class programChange(GenericEvent):
        '''A class that encapsulates a program change event.
        '''
        
        def __init__(self,  channel,  time,  programNumber):
            GenericEvent.__init__(self, time,)
            self.type = 'programChange'
            self.programNumber = programNumber
            self.channel = channel
            
    class SysExEvent(GenericEvent):
        '''A class that encapsulates a System Exclusive  event.
        '''
        
        def __init__(self,  time,  manID,  payload):
            GenericEvent.__init__(self, time,)
            self.type = 'SysEx'
            self.manID = manID
            self.payload = payload
            
    class UniversalSysExEvent(GenericEvent):
        '''A class that encapsulates a Universal System Exclusive  event.
        '''
        
        def __init__(self,  time,  realTime,  sysExChannel,  code,  subcode,  payload):
            GenericEvent.__init__(self, time,)
            self.type = 'UniversalSysEx'
            self.realTime = realTime
            self.sysExChannel = sysExChannel
            self.code = code
            self.subcode = subcode
            self.payload = payload
            
    class ControllerEvent(GenericEvent):
        '''A class that encapsulates a program change event.
        '''
        
        def __init__(self,  channel,  time,  eventType,  parameter1,):
            GenericEvent.__init__(self, time,)
            self.type = 'controllerEvent'
            self.parameter1 = parameter1
            self.channel = channel
            self.eventType = eventType

    class trackName(GenericEvent):
        '''A class that encapsulates a program change event.
        '''
        
        def __init__(self,  time,  trackName):
            GenericEvent.__init__(self, time,)
            self.type = 'trackName'
            self.trackName = trackName

            
    def __init__(self, removeDuplicates,  deinterleave):
        '''Initialize the MIDITrack object.
        '''
        self.headerString = struct.pack('cccc',b'M',b'T',b'r',b'k')
        self.dataLength = 0 # Is calculated after the data is in place
        self.MIDIdata = b""
        self.closed = False
        self.eventList = []
        self.MIDIEventList = []
        self.remdep = removeDuplicates
        self.deinterleave = deinterleave
        
    def addNoteByNumber(self,channel, pitch,time,duration,volume,annotation=None):
        '''Add a note by chromatic MIDI number
        '''
        self.eventList.append(MIDITrack.note(channel, pitch,time,duration,volume,annotation))
        
    def addControllerEvent(self,channel,time,eventType, paramerter1):
        '''
        Add a controller event.
        '''
        
        self.eventList.append(MIDITrack.ControllerEvent(channel,time,eventType, \
                                             paramerter1))
        
    def addTempo(self,time,tempo):
        '''
        Add a tempo change (or set) event.
        '''
        self.eventList.append(MIDITrack.tempo(time,tempo))
        
    def addSysEx(self,time,manID, payload):
        '''
        Add a SysEx event.
        '''
        self.eventList.append(MIDITrack.SysExEvent(time, manID,  payload))
        
    def addUniversalSysEx(self,time,code, subcode, payload,  sysExChannel=0x7F,  \
        realTime=False):
        '''
        Add a Universal SysEx event.
        '''
        self.eventList.append(MIDITrack.UniversalSysExEvent(time, realTime,  \
            sysExChannel,  code,  subcode, payload))
        
    def addProgramChange(self,channel, time, program):
        '''
        Add a program change event.
        '''
        self.eventList.append(MIDITrack.programChange(channel, time, program))
        
    def addTrackName(self,time,trackName):
        '''
        Add a track name event.
        '''
        self.eventList.append(MIDITrack.trackName(time,trackName))
        
    def changeNoteTuning(self,  tunings,   sysExChannel=0x7F,  realTime=False,  \
        tuningProgam=0):
        '''Change the tuning of MIDI notes
        '''
        payload = struct.pack('>B',  tuningProgam)
        payload = payload + struct.pack('>B',  len(tunings))
        for (noteNumber,  frequency) in tunings:
            payload = payload + struct.pack('>B',  noteNumber)
            MIDIFreqency = frequencyTransform(frequency)
            for byte in MIDIFreqency:
                payload = payload + struct.pack('>B',  byte)
                
        self.eventList.append(MIDITrack.UniversalSysExEvent(0, realTime,  sysExChannel,\
            8,  2, payload))
    
    def processEventList(self):
        '''
        Process the event list, creating a MIDIEventList
        
        For each item in the event list, one or more events in the MIDIEvent
        list are created.
        '''
        
        # Loop over all items in the eventList
        
        for thing in self.eventList:
            if thing.type == 'note':
                event = MIDIEvent()
                event.type = "NoteOn"
                event.time = thing.time * TICKSPERBEAT
                event.pitch = thing.pitch
                event.volume = thing.volume
                event.channel = thing.channel
                event.ord = 3
                self.MIDIEventList.append(event)

                event = MIDIEvent()
                event.type = "NoteOff"
                event.time = (thing.time + thing.duration) * TICKSPERBEAT
                event.pitch = thing.pitch
                event.volume = thing.volume
                event.channel = thing.channel
                event.ord = 2
                self.MIDIEventList.append(event)

            elif thing.type == 'tempo':
                event = MIDIEvent()
                event.type = "Tempo"
                event.time = thing.time * TICKSPERBEAT
                event.tempo = thing.tempo
                event.ord = 3
                self.MIDIEventList.append(event)

            elif thing.type == 'programChange':
                event = MIDIEvent()
                event.type = "ProgramChange"
                event.time = thing.time * TICKSPERBEAT
                event.programNumber = thing.programNumber
                event.channel = thing.channel
                event.ord = 1
                self.MIDIEventList.append(event)

            elif thing.type == 'trackName':
                event = MIDIEvent()
                event.type = "TrackName"
                event.time = thing.time * TICKSPERBEAT
                event.trackName = thing.trackName
                event.ord = 0
                self.MIDIEventList.append(event)

            elif thing.type == 'controllerEvent':
                event = MIDIEvent()
                event.type = "ControllerEvent"
                event.time = thing.time * TICKSPERBEAT
                event.eventType = thing.eventType
                event.channel = thing.channel
                event.paramerter1 = thing.parameter1
                event.ord = 1
                self.MIDIEventList.append(event)

            elif thing.type == 'SysEx':
                event = MIDIEvent()
                event.type = "SysEx"
                event.time = thing.time * TICKSPERBEAT
                event.manID = thing.manID
                event.payload = thing.payload
                event.ord = 1
                self.MIDIEventList.append(event)

            elif thing.type == 'UniversalSysEx':
                event = MIDIEvent()
                event.type = "UniversalSysEx"
                event.realTime = thing.realTime
                event.sysExChannel = thing.sysExChannel
                event.time = thing.time * TICKSPERBEAT
                event.code = thing.code
                event.subcode = thing.subcode
                event.payload = thing.payload
                event.ord = 1
                self.MIDIEventList.append(event)

            else:
                print ("Error in MIDITrack: Unknown event type")
                sys.exit(2)
            
        # Assumptions in the code expect the list to be time-sorted.
        # self.MIDIEventList.sort(lambda x, y: x.time - y.time)

        self.MIDIEventList.sort(key=lambda x: (x.time))

        if self.deinterleave:    
            self.deInterleaveNotes()

    def removeDuplicates(self):
        '''
        Remove duplicates from the eventList.
        
        This function will remove duplicates from the eventList. This is necessary
        because we the MIDI event stream can become confused otherwise.
        '''
        
        # For this algorithm to work, the events in the eventList must be hashable 
        # (that is, they must have a __hash__() and __eq__() function defined).
        
        tempDict = {}
        for item in self.eventList:
            tempDict[item] = 1
            
        self.eventList = list(tempDict.keys())
        
        # Sort on type, them on time. Necessary because keys() has no requirement to return
        # things in any order.
        
        self.eventList.sort(key=lambda x: (x.type))
        self.eventList.sort(key=lambda x: (x.time)) #A bit of a hack.

    def closeTrack(self):
        '''Called to close a track before writing
        
        This function should be called to "close a track," that is to
        prepare the actual data stream for writing. Duplicate events are
        removed from the eventList, and the MIDIEventList is created.
        
        Called by the parent MIDIFile object.
        '''

        if self.closed == True:
            return
        self.closed = True
        
        if self.remdep:
            self.removeDuplicates()
            

        self.processEventList()
        
    def writeMIDIStream(self):
        '''
        Write the meta data and note data to the packed MIDI stream.
        '''

        #Process the events in the eventList

        self.writeEventsToStream()

        # Write MIDI close event.

        self.MIDIdata = self.MIDIdata + struct.pack('BBBB',0x00,0xFF, \
            0x2F,0x00)
        
        # Calculate the entire length of the data and write to the header
        
        self.dataLength = struct.pack('>L',len(self.MIDIdata))

    def writeEventsToStream(self):
        '''
        Write the events in MIDIEvents to the MIDI stream.
        '''
        preciseTime = 0.0                   # Actual time of event, ignoring round-off
        actualTime = 0.0                    # Time as written to midi stream, include round-off
        for event in self.MIDIEventList:

            preciseTime = preciseTime + event.time

            # Convert the time to variable length and back, to see how much
            # error is introduced

            testBuffer = bytes()
            varTime = writeVarLength(event.time)
            for timeByte in varTime:
                testBuffer = testBuffer + struct.pack('>B',timeByte)
            (roundedVal,discard) = readVarLength(0,testBuffer)
            roundedTime = actualTime + roundedVal
            # print "Rounded, Precise: %15.10f %15.10f" % (roundedTime, preciseTime)

            # Calculate the delta between the two and apply it to the event time.

            delta = preciseTime - roundedTime
            event.time = event.time + delta

            # Now update the actualTime value, using the updated event time.

            testBuffer = bytes()
            varTime = writeVarLength(event.time)
            for timeByte in varTime:
                testBuffer = testBuffer + struct.pack('>B',timeByte)
            (roundedVal,discard) = readVarLength(0,testBuffer)
            actualTime = actualTime + roundedVal
        
        for event in self.MIDIEventList:
            if event.type == "NoteOn":
                code = 0x9 << 4 | event.channel
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.pitch)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.volume)
            elif event.type == "NoteOff":
                code = 0x8 << 4 | event.channel
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.pitch)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.volume)
            elif event.type == "Tempo":
                code = 0xFF
                subcode = 0x51
                fourbite = struct.pack('>L', event.tempo)
                threebite = fourbite[1:4]       # Just discard the MSB
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',subcode)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', 0x03) # Data length: 3
                self.MIDIdata = self.MIDIdata + threebite
            elif event.type == 'ProgramChange':
                code = 0xC << 4 | event.channel
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.programNumber)
            elif event.type == 'TrackName':
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('B',0xFF) # Meta-event
                self.MIDIdata = self.MIDIdata + struct.pack('B',0X03) # Event Type
                dataLength = len(event.trackName)
                dataLenghtVar = writeVarLength(dataLength)
                for i in range(0,len(dataLenghtVar)):
                    self.MIDIdata = self.MIDIdata + struct.pack("b",dataLenghtVar[i])
                self.MIDIdata = self.MIDIdata + event.trackName.encode()
            elif event.type == "ControllerEvent":
                code = 0xB << 4 | event.channel
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.eventType)
                self.MIDIdata = self.MIDIdata + struct.pack('>B',event.paramerter1)
            elif event.type == "SysEx":
                code = 0xF0
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', code)
                
                payloadLength = writeVarLength(len(event.payload)+2)
                for lenByte in payloadLength:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',lenByte)
                    
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.manID)
                self.MIDIdata = self.MIDIdata + event.payload
                self.MIDIdata = self.MIDIdata + struct.pack('>B',0xF7)
            elif event.type == "UniversalSysEx":
                code = 0xF0
                varTime = writeVarLength(event.time)
                for timeByte in varTime:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',timeByte)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', code)
                
                # Do we need to add a length?
                payloadLength = writeVarLength(len(event.payload)+5)
                for lenByte in payloadLength:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B',lenByte)
                
                if event.realTime :
                    self.MIDIdata = self.MIDIdata + struct.pack('>B', 0x7F)
                else:
                    self.MIDIdata = self.MIDIdata + struct.pack('>B', 0x7E)
                    
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.sysExChannel)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.code)
                self.MIDIdata = self.MIDIdata + struct.pack('>B', event.subcode)
                self.MIDIdata = self.MIDIdata + event.payload
                self.MIDIdata = self.MIDIdata + struct.pack('>B',0xF7)
        
    def deInterleaveNotes(self):
        '''Correct Interleaved notes.
        
        Because we are writing multiple notes in no particular order, we
        can have notes which are interleaved with respect to their start
        and stop times. This method will correct that. It expects that the
        MIDIEventList has been time-ordered.
        '''
        
        tempEventList = []
        stack = {}
        
        for event in self.MIDIEventList:
            
            if event.type == 'NoteOn':
                if str(event.pitch)+str(event.channel) in stack:
                    stack[str(event.pitch)+str(event.channel)].append(event.time)
                else:
                    stack[str(event.pitch)+str(event.channel)] = [event.time]
                tempEventList.append(event)
            elif event.type == 'NoteOff':
                if len(stack[str(event.pitch)+str(event.channel)]) > 1:
                    event.time = stack[str(event.pitch)+str(event.channel)].pop()
                    tempEventList.append(event)
                else:
                    stack[str(event.pitch)+str(event.channel)].pop()
                    tempEventList.append(event)
            else:
                tempEventList.append(event)
                    
        self.MIDIEventList = tempEventList
        
        # A little trickery here. We want to make sure that NoteOff events appear 
        # before NoteOn events, so we'll do two sorts -- on on type, one on time. 
        # This may have to be revisited, as it makes assumptions about how 
        # the internal sort works, and is in essence creating a sort on a primary 
        # and secondary key.
        
        self.MIDIEventList.sort(key=lambda x: (x.type))
        self.MIDIEventList.sort(key=lambda x: (x.time))

    def adjustTime(self,origin):
        '''
        Adjust Times to be relative, and zero-origined
        '''
        
        if len(self.MIDIEventList) == 0:
            return
        tempEventList = []
    
        runningTime = 0 
        
        for event in self.MIDIEventList:
            adjustedTime = event.time - origin
            event.time = adjustedTime - runningTime
            runningTime = adjustedTime
            tempEventList.append(event)
            
        self.MIDIEventList = tempEventList
        
    def writeTrack(self,fileHandle):
        '''
        Write track to disk.
        '''
        
        if not self.closed:
            self.closeTrack()
            
        fileHandle.write(self.headerString)
        fileHandle.write(self.dataLength)
        fileHandle.write(self.MIDIdata)


class MIDIHeader:
    '''
    Class to encapsulate the MIDI header structure.
    
    This class encapsulates a MIDI header structure. It isn't used for much,
    but it will create the appropriately packed identifier string that all
    MIDI files should contain. It is used by the MIDIFile class to create a
    complete and well formed MIDI pattern.
    
    '''
    def __init__(self,numTracks):
        ''' Initialize the data structures
        '''
        self.headerString = struct.pack('cccc',b'M',b'T',b'h',b'd')
        self.headerSize = struct.pack('>L',6)
        # Format 1 = multi-track file
        self.format = struct.pack('>H',1)
        self.numTracks = struct.pack('>H',numTracks)
        self.ticksPerBeat = struct.pack('>H',TICKSPERBEAT)
    

    def writeFile(self,fileHandle):
        fileHandle.write(self.headerString)
        fileHandle.write(self.headerSize)
        fileHandle.write(self.format)
        fileHandle.write(self.numTracks)
        fileHandle.write(self.ticksPerBeat)

class MIDIFile:
    '''Class that represents a full, well-formed MIDI pattern.
    
    This is a container object that contains a header, one or more tracks,
    and the data associated with a proper and well-formed MIDI pattern.
    
    Calling:
    
        MyMIDI = MidiFile(tracks, removeDuplicates=True,  deinterleave=True)
        
        normally
        
        MyMIDI = MidiFile(tracks)
        
    Arguments:
    
        tracks: The number of tracks this object contains
            
        removeDuplicates: If true (the default), the software will remove duplicate
        events which have been added. For example, two notes at the same channel,
        time, pitch, and duration would be considered duplicate.
        
        deinterleave: If True (the default), overlapping notes (same pitch, same
        channel) will be modified so that they do not overlap. Otherwise the sequencing
        software will need to figure out how to interpret NoteOff events upon playback.
    '''
    
    def __init__(self, numTracks, removeDuplicates=True,  deinterleave=True):
        '''
        Initialize the class
        '''
        self.header = MIDIHeader(numTracks)
        
        self.tracks = list()
        self.numTracks = numTracks
        self.closed = False
        
        for i in range(0,numTracks):
            self.tracks.append(MIDITrack(removeDuplicates,  deinterleave))
            
            
    # Public Functions. These (for the most part) wrap the MIDITrack functions, where most
    # Processing takes place.
    
    def addNote(self,track, channel, pitch,time,duration,volume,annotation=None):
        """
        Add notes to the MIDIFile object
        
        Use:
            MyMIDI.addNotes(track,channel,pitch,time, duration, volume)
            
        Arguments:
            track: The track to which the note is added.
            channel: the MIDI channel to assign to the note. [Integer, 0-15]
            pitch: the MIDI pitch number [Integer, 0-127].
            time: the time (in beats) at which the note sounds [Float].
            duration: the duration of the note (in beats) [Float].
            volume: the volume (velocity) of the note. [Integer, 0-127].
        """
        self.tracks[track].addNoteByNumber(channel, pitch, time, duration, volume, annotation)

    def addTrackName(self,track, time,trackName):
        """
        Add a track name to a MIDI track.
        
        Use:
            MyMIDI.addTrackName(track,time,trackName)
            
        Argument:
            track: The track to which the name is added. [Integer, 0-127].
            time: The time at which the track name is added, in beats [Float].
            trackName: The track name. [String].
        """
        self.tracks[track].addTrackName(time,trackName)
        
    def addTempo(self,track, time,tempo):
        """
        Add a tempo event.
        
        Use:
            MyMIDI.addTempo(track, time, tempo)
            
        Arguments:
            track: The track to which the event is added. [Integer, 0-127].
            time: The time at which the event is added, in beats. [Float].
            tempo: The tempo, in Beats per Minute. [Integer]
        """
        self.tracks[track].addTempo(time,tempo)
        
    def addProgramChange(self,track, channel, time, program):
        """
        Add a MIDI program change event.
        
        Use:
            MyMIDI.addProgramChange(track,channel, time, program)
            
        Arguments:
            track: The track to which the event is added. [Integer, 0-127].
            channel: The channel the event is assigned to. [Integer, 0-15].
            time: The time at which the event is added, in beats. [Float].
            program: the program number. [Integer, 0-127].
        """
        self.tracks[track].addProgramChange(channel, time, program)
    
    def addControllerEvent(self,track, channel,time,eventType, paramerter1):
        """
        Add a MIDI controller event.
        
        Use:
            MyMIDI.addControllerEvent(track, channel, time, eventType, parameter1)
            
        Arguments:
            track: The track to which the event is added. [Integer, 0-127].
            channel: The channel the event is assigned to. [Integer, 0-15].
            time: The time at which the event is added, in beats. [Float].
            eventType: the controller event type.
            parameter1: The event's parameter. The meaning of which varies by event type.
        """
        self.tracks[track].addControllerEvent(channel,time,eventType, paramerter1)
        
    def changeNoteTuning(self,  track,  tunings,   sysExChannel=0x7F,  \
                         realTime=False,  tuningProgam=0):
        """
        Change a note's tuning using SysEx change tuning program.
            
        Use:
            MyMIDI.changeNoteTuning(track,[tunings],realTime=False, tuningProgram=0)
            
        Arguments:
            track: The track to which the event is added. [Integer, 0-127].
            tunings: A list of tuples in the form (pitchNumber, frequency). 
                     [[(Integer,Float]]
            realTime: Boolean which sets the real-time flag. Defaults to false.
            sysExChannel: do note use (see below).
            tuningProgram: Tuning program to assign. Defaults to zero. [Integer, 0-127]
            
        In general the sysExChannel should not be changed (parameter will be depreciated).
        
        Also note that many software packages and hardware packages do not implement
        this standard!
        """
        self.tracks[track].changeNoteTuning(tunings,   sysExChannel,  realTime,\
                                              tuningProgam)
  
    def writeFile(self,fileHandle):
        '''
        Write the MIDI File.
        
        Use:
            MyMIDI.writeFile(filehandle)
        
        Arguments:
            filehandle: a file handle that has been opened for binary writing.
        '''
        
        self.header.writeFile(fileHandle)
        
        #Close the tracks and have them create the MIDI event data structures.
        self.close()
        
        #Write the MIDI Events to file.
        for i in range(0,self.numTracks):
            self.tracks[i].writeTrack(fileHandle)

    def addSysEx(self,track, time, manID, payload):
        """
        Add a SysEx event
        
        Use:
            MyMIDI.addSysEx(track,time,ID,payload)
            
        Arguments:
            track: The track to which the event is added. [Integer, 0-127].
            time: The time at which the event is added, in beats. [Float].
            ID: The SysEx ID number
            payload: the event payload.
            
        Note: This is a low-level MIDI function, so care must be used in
        constructing the payload. It is recommended that higher-level helper
        functions be written to wrap this function and construct the payload if
        a developer finds him or herself using the function heavily.
        """
        self.tracks[track].addSysEx(time,manID, payload)
    
    def addUniversalSysEx(self,track,  time,code, subcode, payload,  \
                          sysExChannel=0x7F,  realTime=False):
        """
        Add a Universal SysEx event.
        
        Use:
            MyMIDI.addUniversalSysEx(track, time, code, subcode, payload,\
                                      sysExChannel=0x7f, realTime=False)
                    
        Arguments:
            track: The track to which the event is added. [Integer, 0-127].
            time: The time at which the event is added, in beats. [Float].
            code: The even code. [Integer]
            subcode The event sub-code [Integer]
            payload: The event payload. [Binary string]
            sysExChannel: The SysEx channel.
            realTime: Sets the real-time flag. Defaults to zero.
        
        Note: This is a low-level MIDI function, so care must be used in
        constructing the payload. It is recommended that higher-level helper
        functions be written to wrap this function and construct the payload if
        a developer finds him or herself using the function heavily. As an example
        of such a helper function, see the changeNoteTuning function, both here and
        in MIDITrack.
        """
        
        self.tracks[track].addUniversalSysEx(time,code, subcode, payload,  sysExChannel,\
                                               realTime)
                                               
    def shiftTracks(self,  offset=0):
        """Shift tracks to be zero-origined, or origined at offset.
        
        Note that the shifting of the time in the tracks uses the MIDIEventList -- in other
        words it is assumed to be called in the stage where the MIDIEventList has been
        created. This function, however, it meant to operate on the eventList itself.
        """
        origin = 1000000 # A little silly, but we'll assume big enough

        for track in self.tracks:
                if len(track.eventList) > 0:
                    for event in track.eventList:
                        if event.time < origin:
                            origin = event.time
        
        for track in self.tracks:
            tempEventList = []
            #runningTime = 0 
        
            for event in track.eventList:
                adjustedTime = event.time - origin
                #event.time = adjustedTime - runningTime + offset
                event.time = adjustedTime + offset
                #runningTime = adjustedTime
                tempEventList.append(event)
            
            track.eventList = tempEventList

    #End Public Functions ########################
    
    def close(self):
        '''Close the MIDIFile for further writing.
        
        To close the File for events, we must close the tracks, adjust the time to be
        zero-origined, and have the tracks write to their MIDI Stream data structure.
        '''
        
        if self.closed == True:
            return
                
        for i in range(0,self.numTracks):
            self.tracks[i].closeTrack()
            # We want things like program changes to come before notes when they are at the
            # same time, so we sort the MIDI events by their ordinality
            self.tracks[i].MIDIEventList.sort()
            
        origin = self.findOrigin()

        for i in range(0,self.numTracks):
            self.tracks[i].adjustTime(origin)
            self.tracks[i].writeMIDIStream()
            
        self.closed = True
    
    
    def findOrigin(self):
        '''Find the earliest time in the file's tracks.append.
        '''
        origin = 1000000 # A little silly, but we'll assume big enough

    # Note: This code assumes that the MIDIEventList has been sorted, so this should be insured
    # before it is called. It is probably a poor design to do this. 
    # TODO: -- Consider making this less efficient but more robust by not assuming the list to be sorted.
    
        for track in self.tracks:
                if len(track.MIDIEventList) > 0:
                    if track.MIDIEventList[0].time < origin:
                        origin = track.MIDIEventList[0].time
                        
        
        return origin
            
def writeVarLength(i):
    '''Accept an input, and write a MIDI-compatible variable length stream
    
    The MIDI format is a little strange, and makes use of so-called variable
    length quantities. These quantities are a stream of bytes. If the most
    significant bit is 1, then more bytes follow. If it is zero, then the
    byte in question is the last in the stream
    '''
    input = int(i+0.5)
    output = [0,0,0,0]
    reversed = [0,0,0,0]
    count = 0
    result = input & 0x7F
    output[count] = result
    count = count + 1
    input = input >> 7
    while input > 0:
        result = input & 0x7F 
        result = result | 0x80
        output[count] = result
        count = count + 1
        input = input >> 7  

    reversed[0] = output[3]
    reversed[1] = output[2]
    reversed[2] = output[1]
    reversed[3] = output[0]
    return reversed[4-count:4]
    
def readVarLength(offset, buffer):
    '''A function to read a MIDI variable length variable.

    It returns a tuple of the value read and the number of bytes processed. The
    input is an offset into the buffer, and the buffer itself.
    '''
    toffset = offset
    output = 0
    bytesRead = 0
    while True:
        output = output << 7
        byte = struct.unpack_from('>B',buffer,toffset)[0]
        toffset = toffset + 1
        bytesRead = bytesRead + 1
        output = output + (byte & 127)
        if (byte & 128) == 0:
            break
    return (output, bytesRead)

def frequencyTransform(freq):
    '''Returns a three-byte transform of a frequencyTransform
    '''
    resolution = 16384
    freq = float(freq)
    dollars = 69 + 12 * math.log(freq/(float(440)), 2)
    firstByte = int(dollars)
    lowerFreq = 440 * pow(2.0, ((float(firstByte) - 69.0)/12.0))
    if freq != lowerFreq:
        centDif = 1200 * math.log( (freq/lowerFreq), 2)
    else:
        centDif = 0
    cents = round(centDif/100 * resolution) # round?
    secondByte = min([int(cents)>>7, 0x7F])
    thirdByte = cents - (secondByte << 7)
    thirdByte = min([thirdByte, 0x7f])
    if thirdByte == 0x7f and secondByte == 0x7F and firstByte == 0x7F:
        thirdByte = 0x7e
        
    thirdByte = int(thirdByte)
    return [firstByte,  secondByte,  thirdByte]
    
def returnFrequency(freqBytes):
    '''The reverse of frequencyTransform. Given a byte stream, return a frequency.
    '''
    resolution = 16384.0
    baseFrequency = 440 * pow(2.0, (float(freqBytes[0]-69.0)/12.0))
    frac = (float((int(freqBytes[1]) << 7) + int(freqBytes[2])) * 100.0) / resolution
    frequency = baseFrequency * pow(2.0, frac/1200.0)
    return frequency


def jpg2midi(filePath):
    import sys
    import subprocess
    import cv2
    import time
    import numpy as np
    # from best_fit import fit
    # from rectangle import Rectangle
    # from note import Note
    from random import randint
    # from midiutil.MidiFile3 import MIDIFile
    
    staff_files = [
        "resources/template/staff2.png", 
        "resources/template/staff.png"]
    quarter_files = [
        "resources/template/quarter.png", 
        "resources/template/solid-note.png"]
    sharp_files = [
        "resources/template/sharp.png"]
    flat_files = [
        "resources/template/flat-line.png", 
        "resources/template/flat-space.png" ]
    half_files = [
        "resources/template/half-space.png", 
        "resources/template/half-note-line.png",
        "resources/template/half-line.png", 
        "resources/template/half-note-space.png"]
    whole_files = [
        "resources/template/whole-space.png", 
        "resources/template/whole-note-line.png",
        "resources/template/whole-line.png", 
        "resources/template/whole-note-space.png"]
    
    staff_imgs = [cv2.imread(staff_file, 0) for staff_file in staff_files]
    quarter_imgs = [cv2.imread(quarter_file, 0) for quarter_file in quarter_files]
    sharp_imgs = [cv2.imread(sharp_files, 0) for sharp_files in sharp_files]
    flat_imgs = [cv2.imread(flat_file, 0) for flat_file in flat_files]
    half_imgs = [cv2.imread(half_file, 0) for half_file in half_files]
    whole_imgs = [cv2.imread(whole_file, 0) for whole_file in whole_files]
    
    staff_lower, staff_upper, staff_thresh = 50, 150, 0.77
    sharp_lower, sharp_upper, sharp_thresh = 50, 150, 0.70
    flat_lower, flat_upper, flat_thresh = 50, 150, 0.77
    quarter_lower, quarter_upper, quarter_thresh = 50, 150, 0.70
    half_lower, half_upper, half_thresh = 50, 150, 0.70
    whole_lower, whole_upper, whole_thresh = 50, 150, 0.70
    
    
    def locate_images(img, templates, start, stop, threshold):
        locations, scale = fit(img, templates, start, stop, threshold)
        img_locations = []
        for i in range(len(templates)):
            w, h = templates[i].shape[::-1]
            w *= scale
            h *= scale
            img_locations.append([Rectangle(pt[0], pt[1], w, h) for pt in zip(*locations[i][::-1])])
        return img_locations
    
    def merge_recs(recs, threshold):
        filtered_recs = []
        while len(recs) > 0:
            r = recs.pop(0)
            recs.sort(key=lambda rec: rec.distance(r))
            merged = True
            while(merged):
                merged = False
                i = 0
                for _ in range(len(recs)):
                    if r.overlap(recs[i]) > threshold or recs[i].overlap(r) > threshold:
                        r = r.merge(recs.pop(i))
                        merged = True
                    elif recs[i].distance(r) > r.w/2 + recs[i].w/2:
                        break
                    else:
                        i += 1
            filtered_recs.append(r)
        return filtered_recs
    
    def open_file(path):
        cmd = {'linux':'eog', 'win32':'explorer', 'darwin':'open'}[sys.platform]
        subprocess.run([cmd, path])
    
    if __name__ == "__main__":
        img_file = filePath # sys.argv[1:][0]
        img = cv2.imread(img_file, 0)
        img_gray = img#cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.cvtColor(img_gray,cv2.COLOR_GRAY2RGB)
        ret,img_gray = cv2.threshold(img_gray,127,255,cv2.THRESH_BINARY)
        img_width, img_height = img_gray.shape[::-1]
    
        print("Matching staff image...")
        staff_recs = locate_images(img_gray, staff_imgs, staff_lower, staff_upper, staff_thresh)
    
        print("Filtering weak staff matches...")
        staff_recs = [j for i in staff_recs for j in i]
        heights = [r.y for r in staff_recs] + [0]
        histo = [heights.count(i) for i in range(0, max(heights) + 1)]
        avg = np.mean(list(set(histo)))
        staff_recs = [r for r in staff_recs if histo[r.y] > avg]
    
        print("Merging staff image results...")
        staff_recs = merge_recs(staff_recs, 0.01)
        staff_recs_img = img.copy()
        for r in staff_recs:
            r.draw(staff_recs_img, (0, 0, 255), 2)
        cv2.imwrite('staff_recs_img.png', staff_recs_img)
        # open_file('staff_recs_img.png')
    
        print("Discovering staff locations...")
        staff_boxes = merge_recs([Rectangle(0, r.y, img_width, r.h) for r in staff_recs], 0.01)
        staff_boxes_img = img.copy()
        for r in staff_boxes:
            r.draw(staff_boxes_img, (0, 0, 255), 2)
        cv2.imwrite('staff_boxes_img.png', staff_boxes_img)
        # open_file('staff_boxes_img.png')
        
        print("Matching sharp image...")
        sharp_recs = locate_images(img_gray, sharp_imgs, sharp_lower, sharp_upper, sharp_thresh)
    
        print("Merging sharp image results...")
        sharp_recs = merge_recs([j for i in sharp_recs for j in i], 0.5)
        sharp_recs_img = img.copy()
        for r in sharp_recs:
            r.draw(sharp_recs_img, (0, 0, 255), 2)
        cv2.imwrite('sharp_recs_img.png', sharp_recs_img)
        # open_file('sharp_recs_img.png')
    
        print("Matching flat image...")
        flat_recs = locate_images(img_gray, flat_imgs, flat_lower, flat_upper, flat_thresh)
    
        print("Merging flat image results...")
        flat_recs = merge_recs([j for i in flat_recs for j in i], 0.5)
        flat_recs_img = img.copy()
        for r in flat_recs:
            r.draw(flat_recs_img, (0, 0, 255), 2)
        cv2.imwrite('flat_recs_img.png', flat_recs_img)
        # open_file('flat_recs_img.png')
    
        print("Matching quarter image...")
        quarter_recs = locate_images(img_gray, quarter_imgs, quarter_lower, quarter_upper, quarter_thresh)
    
        print("Merging quarter image results...")
        quarter_recs = merge_recs([j for i in quarter_recs for j in i], 0.5)
        quarter_recs_img = img.copy()
        for r in quarter_recs:
            r.draw(quarter_recs_img, (0, 0, 255), 2)
        cv2.imwrite('quarter_recs_img.png', quarter_recs_img)
        # open_file('quarter_recs_img.png')
    
        print("Matching half image...")
        half_recs = locate_images(img_gray, half_imgs, half_lower, half_upper, half_thresh)
    
        print("Merging half image results...")
        half_recs = merge_recs([j for i in half_recs for j in i], 0.5)
        half_recs_img = img.copy()
        for r in half_recs:
            r.draw(half_recs_img, (0, 0, 255), 2)
        cv2.imwrite('half_recs_img.png', half_recs_img)
        # open_file('half_recs_img.png')
    
        print("Matching whole image...")
        whole_recs = locate_images(img_gray, whole_imgs, whole_lower, whole_upper, whole_thresh)
    
        print("Merging whole image results...")
        whole_recs = merge_recs([j for i in whole_recs for j in i], 0.5)
        whole_recs_img = img.copy()
        for r in whole_recs:
            r.draw(whole_recs_img, (0, 0, 255), 2)
        cv2.imwrite('whole_recs_img.png', whole_recs_img)
        # open_file('whole_recs_img.png')
    
        note_groups = []
        for box in staff_boxes:
            staff_sharps = [Note(r, "sharp", box) 
                for r in sharp_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            staff_flats = [Note(r, "flat", box) 
                for r in flat_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            quarter_notes = [Note(r, "4,8", box, staff_sharps, staff_flats) 
                for r in quarter_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            half_notes = [Note(r, "2", box, staff_sharps, staff_flats) 
                for r in half_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            whole_notes = [Note(r, "1", box, staff_sharps, staff_flats) 
                for r in whole_recs if abs(r.middle[1] - box.middle[1]) < box.h*5.0/8.0]
            staff_notes = quarter_notes + half_notes + whole_notes
            staff_notes.sort(key=lambda n: n.rec.x)
            staffs = [r for r in staff_recs if r.overlap(box) > 0]
            staffs.sort(key=lambda r: r.x)
            note_color = (randint(0, 255), randint(0, 255), randint(0, 255))
            note_group = []
            i = 0; j = 0;
            while(i < len(staff_notes)):
                if (staff_notes[i].rec.x > staffs[j].x and j < len(staffs)):
                    r = staffs[j]
                    j += 1;
                    if len(note_group) > 0:
                        note_groups.append(note_group)
                        note_group = []
                    note_color = (randint(0, 255), randint(0, 255), randint(0, 255))
                else:
                    note_group.append(staff_notes[i])
                    staff_notes[i].rec.draw(img, note_color, 2)
                    i += 1
            note_groups.append(note_group)
    
        for r in staff_boxes:
            r.draw(img, (0, 0, 255), 2)
        for r in sharp_recs:
            r.draw(img, (0, 0, 255), 2)
        flat_recs_img = img.copy()
        for r in flat_recs:
            r.draw(img, (0, 0, 255), 2)
            
        cv2.imwrite('res.png', img)
        open_file('res.png')
    
        for note_group in note_groups:
            print([ note.note + " " + note.sym for note in note_group])
    
        midi = MIDIFile(1)
        
        track = 0   
        time = 0
        channel = 0
        volume = 100
        
        midi.addTrackName(track, time, "Track")
        midi.addTempo(track, time, 140)
        
        for note_group in note_groups:
            duration = None
            for note in note_group:
                note_type = note.sym
                if note_type == "1":
                    duration = 4
                elif note_type == "2":
                    duration = 2
                elif note_type == "4,8":
                    duration = 1 if len(note_group) == 1 else 0.5
                pitch = note.pitch
                midi.addNote(track,channel,pitch,time,duration,volume)
                time += duration
    
        midi.addNote(track,channel,pitch,time,4,0)
        # And write it to disk.
        binfile = open("output.mid", 'wb')
        midi.writeFile(binfile)
        binfile.close()
        open_file('output.mid')
        
jpg2midi("/Users/emma/Documents/15-112/112tp/SheetVision/resources/samples/fire.jpg")
