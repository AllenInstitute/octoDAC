# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import numpy as np
import pyvisa as visa

import matplotlib.pyplot as plt

import time

from octoDAC.driver import octoDACDriver

from nicoLase import NicoLaseDriver

def rgb(r, g, b):
    return [float(r)/255, float(g)/255, float(b)/255] 


def rigol_startOscope(timeout = 20000, chunk_size = 1024000):

    rm = visa.ResourceManager()
    
    rm.timeout = timeout
    rm.chunk_size = chunk_size
    
    instID = rm.list_resources()[0]
    
    scope = rm.open_resource(instID)
    
    return scope, rm




def rigol_pullData(scope, channel):

    # https://gist.github.com/StevanxDK/4e6f74162f721f608b0e4993070ccbd2
    # scope.write('STOP')
    
    
    # Make sure channel can be 'CH1' or 'CHAN1'  and work here
    # channel = 'CHAN' + channel[-1]
    
    sample_rate = scope.query_ascii_values(':ACQ:SRAT?')[0]
    # Select CH1
    scope.write(":WAV:SOUR " + channel)
    
    # Y origin for wav data
    YORigin = scope.query_ascii_values(":WAV:YOR?")[0]
    # Y REF for wav data
    YREFerence = scope.query_ascii_values(":WAV:YREF?")[0]
    # Y INC for wav data
    YINCrement = scope.query_ascii_values(":WAV:YINC?")[0]
    
    # X origin for wav data
    XORigin = scope.query_ascii_values(":WAV:XOR?")[0]
    # X REF for wav data
    XREFerence = scope.query_ascii_values(":WAV:XREF?")[0]
    # X INC for wav data
    XINCrement = scope.query_ascii_values(":WAV:XINC?")[0]
    
    # Get time base to calculate memory depth.
    time_base = scope.query_ascii_values(":TIM:SCAL?")[0]
    # Calculate memory depth for later use.
    memory_depth = (time_base*12) * sample_rate
    
    # Set the waveform reading mode to RAW.
    scope.write(":WAV:MODE RAW")
    # Set return format to Byte.
    scope.write(":WAV:FORM BYTE")
    
    # Set waveform read start to 0.
    scope.write(":WAV:STAR 1")
    # Set waveform read stop to 250000.
    scope.write(":WAV:STOP 250000")
    
    # Read data from the scope, excluding the first 9 bytes (TMC header).
    rawdata = scope.query_binary_values(":WAV:DATA?", datatype='B')
    
    # Check if memory depth is bigger than the first data extraction.
    if (memory_depth > 250000):
    	loopcount = 1
    	# Find the maximum number of loops required to loop through all memory.
    	loopmax = np.ceil(memory_depth/250000)
    	while (loopcount < loopmax):
    		# Calculate the next start of the waveform in the internal memory.
    		start = (loopcount*250000)+1
    		scope.write(":WAV:STAR {0}".format(start))
    		# Calculate the next stop of the waveform in the internal memory
    		stop = (loopcount+1)*250000
    		print(stop)
    		scope.write(":WAV:STOP {0}".format(stop))
    		# Extent the rawdata variables with the new values.
    		rawdata.extend(scope.query_binary_values(":WAV:DATA?", datatype='B'))
    		loopcount = loopcount+1
    
    
    data = (np.asarray(rawdata) - YORigin - YREFerence) * YINCrement
    
    # Calcualte data size for generating time axis
    data_size = len(data)
    # Create time axis
    time = np.linspace(XREFerence, XINCrement*data_size, data_size)

    return data, time


def timeAxis_rigol(time):
    # See if we should use a different time axis
    if (time[-1] < 1e-3):
        time = time * 1e6
        tUnit = "µS"
    elif (time[-1] < 1):
        time = time * 1e3
        tUnit = "mS"
    else:
    	tUnit = "S"
        
    return time, tUnit


def makePlots_rigol(tVals, data1, data2, tUnit, trigColor = rgb(52, 152, 219), testColor = rgb(231, 76, 60)):
    
    # Graph data with pyplot.
    plotHandle = plt.plot(tVals, data1, color = trigColor)
    plt.plot(tVals, data2, color = testColor)
    #plot.title("Oscilloscope Channel 1")
    plt.ylabel("Voltage (V)")
    plt.xlabel("Time (" + tUnit + ")")
    plt.xlim(tVals[0], tVals[-1])
    plt.subplots_adjust(left=0.1,top=0.98,bottom=0.1,right=0.8)
    plt.show()
    
    return plotHandle



scope, rm = rigol_startOscope()
print(scope.query('*IDN?'))

#%% Triggering device
# Set up as NicoLase w/ octoDAC_NicoLase_combo.ino sketch

ser1 = NicoLaseDriver.nicoLaseStart('COM4', 115200, 1)
n1 = NicoLaseDriver.NicoLaseDriver(ser1, verbose = True)

#%% Test device
# Set up as NicoLase + octoDAC stack 
# octoDAC_NicoLase_combo.ino sketch loaded 

ser2 = octoDACDriver.octoDACStart('COM3', 115200, 1)

o2 = octoDACDriver.octoDACDriver(ser2, verbose = True)
n2 = NicoLaseDriver.NicoLaseDriver(ser2, verbose = True)

#%%
    # CH1 is trgDev output in pre-acquisition sequence
    # Trigger scope on External rise
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is octoDAC CHAN1 output
    #
    # set o'scope to 50 ms/div
    # set values from 2V45 - 2V55, with 8 unit steps.  
    # Values in 16 bit are 32112 - 33432 (1320 unit change)
    # In 8 unit steps this is 165 steps
    
maxRange = 1200 # points to include
    
startVal = 3276 # amplitude units
stepSize = 8
nSteps = 165



n1.setPreCollectionSeq(0b111111)
n1.setPreSeqExTime(3)

dVals = np.zeros((nSteps, 3))
mVals = np.zeros((nSteps, 3))

for k in range(nSteps):
    
    valNow = startVal + k*stepSize
    o2.setChannel(1, valNow)
    time.sleep(0.5)
    n1.callPreSeq()

   # data1, tVals = rigol_pullData(scope, 'CHAN1')
    data2, tVals = rigol_pullData(scope, 'CHAN2')
    

    tVals, tUnit = timeAxis_rigol(tVals)

    dVals[k, 0] = 5*float(valNow)/65535
    dVals[k, 1] = np.mean(data2[-maxRange:])
    dVals[k, 2] = np.std(data2[-maxRange:])
    
    # data3, tVals = rigol_pullData(scope, 'MATH')
    
    # mVals[k, 0] = valNow
    # mVals[k, 1] = np.mean(data3[-maxRange:])
    # mVals[k, 2] = np.std(data3[-maxRange:])

    #pHand = makePlots_rigol(tVals[0:maxRange], data1[0:maxRange], data2[0:maxRange], tUnit)
    
plt.plot()
plt.errorbar(dVals[:,0], dVals[:,1], yerr = dVals[:,2], fmt = '.', 
             color = rgb(52, 152, 219), markersize = 4)
# plt.errorbar(mVals[:,0], mVals[:,1], yerr = mVals[:,2], fmt = '.', 
#              color = rgb(152, 52, 219), markersize = 4)

plt.show()

#%%


ser1.close()
ser2.close()
del(n1)
del(n2)
del(o2)


