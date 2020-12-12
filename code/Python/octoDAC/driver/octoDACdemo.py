# -*- coding: utf-8 -*-
"""
Created on Tue Apr 14 13:59:02 2020

@author: Rusty Nicovich
"""

import serial
import time
from octoDACDriver import octoDACDriver
import numpy as np

comPort = 'COM3'
baud = 115200
timeOut = 1

serObj = serial.Serial(comPort, baud, timeout = timeOut)
time.sleep(3)
serObj.flushInput()
serObj.reset_input_buffer()

#%%
# Initialize octoDAC object
oD = octoDACDriver(serObj, verbose = True)

# Set Chan1 to full output
oD.setChannel(1, 65535)

# Query shutter state
shutterState = oD.queryShutter()
if shutterState == '1':
    print('Shutter open')
elif shutterState == '0':
    print('Shutter closed')
 
# Close shutter
oD.closeShutter()

# Query shutter state again
shutterState = oD.queryShutter()
if shutterState == '1':
    print('Shutter open')
elif shutterState == '0':
    print('Shutter closed')
    

    
# Upload a simple waveform on Chan2
waveArray = np.array([[2, 0, 0], 
                     [2, 500000, 65535],
                     [2, 1000000, 0]])
 
oD.clearWaveform()
oD.uploadWaveform(waveArray)    
oD.freeRunWaveform()

oD.echoWaveform()


#%%
serObj.close()