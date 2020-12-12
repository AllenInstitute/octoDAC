# -*- coding: utf-8 -*-
"""
Created on Fri May  8 15:32:33 2020

@author: Rusty Nicovich

Requires:
    - TekVISA 4.2.0
    https://www.tek.com/oscilloscope/tds7054-software/tekvisa-connectivity-software-v420
    - pyvisa-py
    


"""

import pyvisa
import numpy as np
from struct import unpack
import pandas as pd
import matplotlib.pyplot as plt
import os
import time

from octoDAC.driver import octoDACDriver

from nicoLase import NicoLaseDriver

config = {'oScopeType' :'RIGOL', # 'RIGOL' or 'TEKTRONIX'
          'dataPoints' : 1371}


def rgb(r, g, b):
    return [float(r)/255, float(g)/255, float(b)/255] 


def acquire(channel, scope, maxTime = []):
    
    if config['oScopeType'] == 'RIGOL':

        tVals, data = rigol_pullData(scope, channel)
        
    elif config['oScopeType'] == 'TEKTRONIX':
        
        tVals, data = tektronix_pullData(scope, channel)
        
    else:
        print('Scope type must be RIGOL or TEKTRONIX')
        tVals = -1
        data = -1
        
        
    if maxTime:
        print('cut down to max time')
        # Cut data down to max time value only
        data = np.delete(data, np.where(tVals > maxTime), axis = 0)
        tVals = np.delete(tVals, np.where(tVals > maxTime))
        
        
    return tVals, data
    
def rigol_pullData(scope, channel):

    # https://gist.github.com/StevanxDK/4e6f74162f721f608b0e4993070ccbd2
    # scope.write('STOP')
    
    
    # Make sure channel can be 'CH1' or 'CHAN1'  and work here
    channel = 'CHAN' + channel[-1]
    
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
    rawdata = scope.query_binary_values(":WAV:DATA?", datatype='B', data_points = config['dataPoints'])
    
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
    tVals = np.linspace(XREFerence, XINCrement*data_size, data_size) - XORigin

    return tVals, data   
    
def tektronix_pullData(scope, channel):
    try:
        scope.write("DATA:SOURCE " + channel)
        scope.write('wfmo:byt_n 2')
        ymult = float(scope.query('WFMPRE:YMULT?'))
        yzero = float(scope.query('WFMPRE:YZERO?'))
        yoff = float(scope.query('WFMPRE:YOFF?'))
        xincr = float(scope.query('WFMPRE:XINCR?'))
        xdelay = float(scope.query('HORizontal:POSition?'))
        scope.write('CURVE?')
        data = scope.read_raw()
        headerlen = 2 + int(data[1])
        header = data[:headerlen]
        ADC_wave = data[headerlen:-1]
        ADC_wave = np.array(unpack('%sB' % len(ADC_wave),ADC_wave))
        Volts = (ADC_wave - yoff) * ymult  + yzero.as_integer_ratio()
        Time = np.arange(0, (xincr * len(Volts)), xincr)-((xincr * len(Volts))/2-xdelay)
        return Time,Volts
    except IndexError:
        return 0,0
    
def timeAxis_rigol(tVals):
    # See if we should use a different time axis
    if (tVals[-1] < 1e-3):
        tVals = tVals * 1e6
        tUnit = "µS"
    elif (tVals[-1] < 1):
        tVals = tVals * 1e3
        tUnit = "mS"
    else:
    	tUnit = "S"
        
    return time, tUnit


def makePlots_rigol(time, data1, data2, tUnit, trigColor = rgb(52, 152, 219), testColor = rgb(231, 76, 60)):
    
    # Graph data with pyplot.
    plotHandle = plt.plot(time, data1, color = trigColor)
    plt.plot(time, data2, color = testColor)
    #plot.title("Oscilloscope Channel 1")
    plt.ylabel("Voltage (V)")
    plt.xlabel("Time (" + tUnit + ")")
    plt.xlim(time[0], time[-1])
    plt.subplots_adjust(left=0.1,top=0.98,bottom=0.1,right=0.8)
    plt.show()
    
    return plotHandle
    

def deviceTest(trgDev, testDev, testType, testRepeats, scopePort, channel = 1, maxTime = []):
    
    testArray = np.zeros((config['dataPoints'], testRepeats*3))
    
    trgDev.setPreCollectionSeq(0b111111)
    trgDev.setPreSeqExTime(3)
    
    if (testType == 'digitalJitter'):
        # Jitter between triggering NicoLase out and test NicoLase output
        # CH1 is trgDev output in pre-acquisition sequence
        # trgDev output in pre-acq seq -> testDev MASTERFIRE
        # CH2 is any testDev output on Nicolase
        #
        # Set o'scope to ~2.5 µs/div horz
         
        testDev.clearSeqs()
        testDev.allOnSeq()
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
            val1 = acquire("CH1", scopePort)
            val2 = acquire("CH2", scopePort)
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
            #time.sleep(1)
            
    elif (testType == 'analogJitter'):
        
        testDev.clearWaveform()
        
        waveForm = np.array([[1, 0, 65535],
                     [1, 10000, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.waveformOnTrigger()
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
        
            val1 = acquire("CH1", scopePort)
            val2 = acquire("CH2", scopePort)
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    
    
    elif (testType == 'tophatJitter'):
        testDev.clearWaveform()
        
        waveForm = np.array([[1, 0, 65535],
                     [1, 100, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.waveformOnTrigger()
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
        
            val1 = acquire("CH1", scopePort)
            val2 = acquire("CH2", scopePort)
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
    
    
    elif (testType == 'analogCycleJitter'):
        testDev.clearWaveform()
        
        waveForm = np.array([[1, 0, 65535],
                     [1, 1000000, 0],
                     [1, 1000100, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.freeRunWaveform()
        
        time.sleep(0.5)
        
        for k in range(testRepeats):
        
            val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'analogJitterAllChannels'):
        
        testDev.clearWaveform()
        
        waveForm = np.array([[1, 0, 65535],
                             [2, 0, 65535],
                             [3, 0, 65535],
                             [4, 0, 65535],
                             [5, 0, 65535],
                             [6, 0, 65535],
                             [7, 0, 65535],
                             [8, 0, 65535],
                             [1, 10000, 0],
                             [2, 10000, 0],
                             [3, 10000, 0],
                             [4, 10000, 0],
                             [5, 10000, 0],
                             [6, 10000, 0],
                             [7, 10000, 0],
                             [8, 10000, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.waveformOnTrigger()
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
        
            val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'topHatJitterAllChannels'):
        
        testDev.clearWaveform()
        
        waveForm = np.array([[1, 0, 65535],
                             [2, 0, 65535],
                             [3, 0, 65535],
                             [4, 0, 65535],
                             [5, 0, 65535],
                             [6, 0, 65535],
                             [7, 0, 65535],
                             [8, 0, 65535],
                             [1, 100, 0],
                             [2, 100, 0],
                             [3, 100, 0],
                             [4, 100, 0],
                             [5, 100, 0],
                             [6, 100, 0],
                             [7, 100, 0],
                             [8, 100, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.waveformOnTrigger()
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
        
            val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'topHatJitterAllChansLonger'):
        
        testDev.clearWaveform()
        
        waveForm = np.array([[1, 0, 65535],
                             [2, 0, 65535],
                             [3, 0, 65535],
                             [4, 0, 65535],
                             [5, 0, 65535],
                             [6, 0, 65535],
                             [7, 0, 65535],
                             [8, 0, 65535],
                             [1, 500, 0],
                             [2, 500, 0],
                             [3, 500, 0],
                             [4, 500, 0],
                             [5, 500, 0],
                             [6, 500, 0],
                             [7, 500, 0],
                             [8, 500, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.waveformOnTrigger()
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
        
            val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'waveformNaive'):
        
        testDev.clearWaveform()
        
        waveForm = np.array([[1, 0, 65535],
                             [1, 200, 0],
                             [1, 400, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.freeRunWaveform()
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
        
            val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'waveformCorrected'):
        
        testDev.clearWaveform()
        
        # # Subtract dead time for Arduino
        # waveForm = np.array([[1, 0, 65535],
        #                      [1, 200, 0],
        #                      [1, 338, 0]])
    
        # Subtract dead time for Arduino
        waveForm = np.array([[1, 0, 65535],
                              [1, 200, 0],
                              [1, 388, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.freeRunWaveform()
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
        
            val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'linearity'):
        testDev.clearWaveform()
        
        stepSize = int(65535/(testRepeats-1))
                
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
         
        for k in range(testRepeats):
            print('Set channel ' + str(channel) + ' to ' + str(k*stepSize))
            testDev.setChannel(channel, (k)*stepSize)
            time.sleep(1)
            # trgDev.callPreSeq()
            time.sleep(1)

           # val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            testArray[:,3*k+0] = val2[0]
            #testArray[:,3*k+1] = np.ones_like(val1[1])*(k)*stepSize
            testArray[:,3*k+1] = 5*float(k*stepSize)/65535
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'stepResolution'):
        
        # set values from 2V45 - 2V55, with 8 unit steps.  
        # Values in 16 bit are 32112 - 33432 (1320 unit change)
        # In 8 unit steps this is 165 steps
        
        stepSize = 8
        
        # testDev.setChannel(channel, 32112)
        testDev.setChannel(channel, 3276)
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
            
        for k in range(testRepeats):
            testDev.setChannel(channel, 3276+(k)*stepSize)
            time.sleep(1)
            
            # trgDev.callPreSeq()
            # time.sleep(1)
            # val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            testArray[:,3*k+0] = val2[0]
#            testArray[:,3*k+1] = np.ones_like(val1[1])*(k)*stepSize
            testArray[:,3*k+1] = 5*float(k*stepSize)/65535
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'sineWaveSingle'):
        
        # Single 0-5v sine wave, fast as possible w/ 2048 samples/channel
        
        nSamplesPerPeriod = 100
        nPeriods = 1
        
        # Make discretized sine wave
        xVals = np.linspace(0, 2*np.pi*nPeriods, nSamplesPerPeriod*nPeriods)
        yVals = (65535*(0.5*np.sin(xVals)+0.5)).astype('uint16')
        
        # [[chan time value]]
        waveArray = np.vstack((np.ones((nSamplesPerPeriod*nPeriods)).T, 
                       np.linspace(0, nSamplesPerPeriod*nPeriods, nSamplesPerPeriod*nPeriods), 
                       yVals)).T.astype('uint16')
        testDev.clearWaveform()
        testDev.uploadWaveform(waveArray)
        
        # Wait for upload to finish
        uploadCheck = testDev.echoWaveform()
               
        testDev.waveformOnTrigger()
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
            
        for k in range(testRepeats):
            
            trgDev.callPreSeq()
            # time.sleep(1)
            val1 = acquire("CH1", scopePort, maxTime = maxTime)
            val2 = acquire("CH2", scopePort, maxTime = maxTime)
            
            testArray[:,3*k+0] = val2[0]
#            testArray[:,3*k+1] = np.ones_like(val1[1])*(k)*stepSize
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
    
    else:
        print('Incorrect test type')
    
    
    return testArray

def rgb(r, g, b):
    return [float(r)/255, float(g)/255, float(b)/255]

def plotTestArray(testArray, saveDest, returnHandle = False):
    trigColor = rgb(52, 152, 219)
    testColor = rgb(231, 76, 60)
    
    for k in range(int(testArray.shape[1]/3)):
        print(k)
        plt.plot(testArray[:,3*k], testArray[:,3*k+1], alpha = np.sqrt(1./(testArray.shape[1]/3)), color = trigColor)
        plt.plot(testArray[:,3*k], testArray[:,3*k+2], alpha = np.sqrt(1./(testArray.shape[1]/3)), color = testColor)
    plt.ylabel('V')
    plt.xlabel('time (s)')
    plt.ticklabel_format(axis="x", style="sci", scilimits=(0,0))
    leg = plt.legend(('Trigger', 'Test'))
    for lh in leg.legendHandles: 
        lh.set_alpha(1)
        
    plt.savefig(saveDest, bbox_inches='tight', dpi = 300)
    plt.show()
    
    if returnHandle:
        return plt.gca()
    
    
def startOscope(timeout = 20000, chunk_size = 1024000):

    rm = pyvisa.ResourceManager()
    
    rm.timeout = timeout
    rm.chunk_size = chunk_size
    
    instID = rm.list_resources()[0]
    
    scope = rm.open_resource(instID)
    
    return scope, rm
    
#%%
def main():

    #%%
    scope, rm = startOscope()

    #%% Triggering device
    # Set up as NicoLase w/ octoDAC_NicoLase_combo.ino sketch
    
    ser1 = NicoLaseDriver.nicoLaseStart('COM4', 115200, 1)
    n1 = NicoLaseDriver.NicoLaseDriver(ser1, verbose = True)
    
    #%% Test device
    # Set up as NicoLase + octoDAC stack 
    # octoDAC_NicoLase_combo.ino sketch loaded 
    
    ser2 = octoDACDriver.octoDACStart('COM7', 115200, 1)
    
    o2 = octoDACDriver.octoDACDriver(ser2, verbose = True)
    n2 = NicoLaseDriver.NicoLaseDriver(ser2, verbose = True)
    
    #%% Digital jitter test
    # Jitter between triggering NicoLase out and test NicoLase output
    # CH1 is trgDev output in pre-acquisition sequence
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is any testDev output on Nicolase
    #
    # Set o'scope to ~2.5 µs/div horz
    
    testType = 'digitalJitter'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, n2, testType, nTestRepeats, scope)
    plotTestArray(testArray, os.path.join('.\output', testType + 'CH1.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + 'CH1.csv'), header = False)
    
    
    #%% 
    # Jitter between triggering NicoLase out and test octoDAC 
    # CH1 is trgDev output in pre-acquisition sequence
    # Trigger scope on rise of trigDev output
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is octoDAC CHAN1 output
    #
    # Input : waveArray - numpy array, M x 3.  
    #   [{channel, timepoint, amplitude],...]
    
    # Set o'scope to ~10.0 µs/div horz
    
    testType = 'analogJitter'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    
    #%% 
    # Jitter between rise and fall of octoDAC top hat
    # CH1 is trgDev output in pre-acquisition sequence
    # Scope trigger is rise of octoDAC output
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is octoDAC CHAN1 output
    #
    
    # Set o'scope to 25.0 µs/div horz
    
    testType = 'tophatJitter'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%% 
    # Jitter between fall of octoDAC top hat and rise on next Arduino loop
    # Invoke with freerun mode 
    # Scope trigger is fall of octoDAC output
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is octoDAC CHAN1 output
    #
    
    # Set o'scope to 25.0 µs/div horz
    
    testType = 'analogCycleJitter'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%% 
    # Jitter between triggering NicoLase out and test octoDAC, with sequences on all channels.
    # Trigger scope on nicoLase output, but in ExtTrigger.  Won't be displayed.
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH1 is octoDAC CHAN8 output
    # CH2 is octoDAC CHAN1 output
    #
    # Input : waveArray - numpy array, M x 3.  
    #   [{channel, timepoint, amplitude],...]
    
    # Set o'scope to ~50.0 µs/div horz
    
    testType = 'analogJitterAllChannels'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%% 
    # Jitter between rise and fall of octoDAC top hat, with waveforms on all channels
    # CH1 is trgDev output in pre-acquisition sequence
    # Trigger scope on nicoLase output, but in ExtTrigger.  Won't be displayed.
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH1 is octoDAC CHAN8 output
    # CH2 is octoDAC CHAN1 output
    #
    # Input : waveArray - numpy array, M x 3.  
    #   [{channel, timepoint, amplitude],...]
    
    # Set o'scope to ~100.0 µs/div horz
    
    testType = 'topHatJitterAllChannels'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope, maxTime = 1e-3)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    
    #%% 
    # Jitter between rise and fall of octoDAC top hat, with waveforms on all channels, cycle > 350 µsec
    # CH1 is trgDev output in pre-acquisition sequence
    # Trigger scope on nicoLase output, but in ExtTrigger.  Won't be displayed.
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH1 is octoDAC CHAN8 output
    # CH2 is octoDAC CHAN1 output
    #
    # Input : waveArray - numpy array, M x 3.  
    #   [{channel, timepoint, amplitude],...]
    
    # Set o'scope to ~100.0 µs/div horz
    
    testType = 'topHatJitterAllChansLonger'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope, maxTime = 1.75e-3)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%% 
    # Demo fixing waveform 'dead time' when cycle needs to complete.
    # CH1 is trgDev output in pre-acquisition sequence
    # Trigger scope on Ch2 rise
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is octoDAC CHAN1 output
    #
    # Input : waveArray - numpy array, M x 3.  
    #   [{channel, timepoint, amplitude],...]
    
    # Set o'scope to ~100.0 µs/div horz
    
    testType = 'waveformNaive'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope, maxTime = 2e-3)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%% 
    # Demo fixing waveform 'dead time' when cycle needs to complete.
    # CH1 is trgDev output in pre-acquisition sequence
    # Trigger scope on Ch2 rise
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is octoDAC CHAN1 output
    #
    # Input : waveArray - numpy array, M x 3.  
    #   [{channel, timepoint, amplitude],...]
    
    # Set o'scope to ~100.0 µs/div horz
    
    testType = 'waveformCorrected'
    nTestRepeats = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope, maxTime = 2e-3)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%%
    # Linearity of signal from specified value -> scope
    # Each cycle, take a step of 65000/nTestRepeats units.  
    
    # Remainging noise ripple at different input values
    # Use output of 'linearity' measurement. 
    
    
    # CH1 is trgDev output in pre-acquisition sequence
    # Trigger scope on External
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is octoDAC CHAN1 output
    #
    # Set o'scope to ~50 ms/div horz
    # Change output channel plugged into scope, channel variable, and channel argument 
    # to sample all channels.
    #
    # Do again w/ ~1 ms/div and AC coupling to look at noise explicitly ('chanx_fast')
    
    testType = 'linearity'
    nTestRepeats = 100
    
    channel = 'chan1'
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope, channel = 1, maxTime = 15e-3)
    plotTestArray(testArray, os.path.join('.\output', testType + '_' + channel + '_Vin.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '_' + channel + '_Vin.csv'), header = False)
    
    
    #%%
    # Resolution of small steps
    # Figure ~1 mV of noise left in signal
    # ~13 bit discrimination gives ~0.6 mV steps
    # Is a step of 8 units at 16 bit resolution 
    
    # CH1 is trgDev output in pre-acquisition sequence
    # Trigger scope on External rise
    # trgDev output in pre-acq seq -> testDev MASTERFIRE
    # CH2 is octoDAC CHAN1 output
    #
    # set o'scope to 50 ms/div
    # set values from 2V45 - 2V55, with 8 unit steps.  
    # Values in 16 bit are 32112 - 33432 (1320 unit change)
    # In 8 unit steps this is 165 steps
    
    testType = 'stepResolution'
    nTestRepeats = 165
    #
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%% Complex waveforms - sine wave
    # Want a sine wave at 2048 points/cycle resolution
    # Do single-shot waveforms after trigger
    # See how fast this can go
    
    testType = 'sineWaveSingle'
    nTestRepeats  = 100
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, scope, maxTime = 2e-3)
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%%
    nSamplesPerPeriod = 100
    nPeriods = 1
    
    # Make discretized sine wave
    xVals = np.linspace(0, 2*np.pi*nPeriods, nSamplesPerPeriod*nPeriods)
    yVals = (65535*(0.5*np.sin(xVals)+0.5)).astype('uint16')
    
    # [[chan time value]]
    waveArray = np.vstack((np.ones((nSamplesPerPeriod*nPeriods)).T, 
                   np.linspace(0, nSamplesPerPeriod*nPeriods, nSamplesPerPeriod*nPeriods), 
                   yVals)).T.astype('uint16')
    o2.clearWaveform()
    # o2.uploadWaveform(waveArray)
    
    # Run via USB
    for k in waveArray:
        o2.setChannel(k[0], k[2])
    
    #%%
    ser1.close()
    ser2.close()

if __name__ == "__main__":
    main()