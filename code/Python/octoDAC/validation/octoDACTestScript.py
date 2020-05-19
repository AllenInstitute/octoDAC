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


def acquire(channel, port):
    try:
        scope = rm.open_resource(port)
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
        Volts = (ADC_wave - yoff) * ymult  + yzero
        Time = np.arange(0, (xincr * len(Volts)), xincr)-((xincr * len(Volts))/2-xdelay)
        return Time,Volts
    except IndexError:
        return 0,0
    

def deviceTest(trgDev, testDev, testType, testRepeats, scopePort, channel = 1):
    
    testArray = np.zeros((2500, testRepeats*3))
    
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
        
            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            
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
        
            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            
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
        
            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            
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
        
            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            
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
        
            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            
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
        
            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            
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
        
            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'waveformCorrected'):
        
        testDev.clearWaveform()
        
        waveForm = np.array([[1, 0, 65535],
                             [1, 200, 0],
                             [1, 338, 0]])
    
        testDev.uploadWaveform(waveForm)
        testDev.freeRunWaveform()
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
        
        for k in range(testRepeats):
            trgDev.callPreSeq()
        
            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            
            testArray[:,3*k+0] = val1[0]
            testArray[:,3*k+1] = val1[1]
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'linearity'):
        
        
        stepSize = 65535/(testRepeats-1)
        
        testDev.setChannel(channel, 0)
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
            
        for k in range(testRepeats):
            testDev.setChannel(channel, (k)*stepSize)
            time.sleep(0.5)
            
            trgDev.callPreSeq()

            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            testArray[:,3*k+0] = val1[0]
#            testArray[:,3*k+1] = np.ones_like(val1[1])*(k)*stepSize
            testArray[:,3*k+1] = 5*float(k*stepSize)/65535
            testArray[:,3*k+2] = val2[1]
            
    elif (testType == 'stepResolution'):
        
        # set values from 2V45 - 2V55, with 8 unit steps.  
        # Values in 16 bit are 32112 - 33432 (1320 unit change)
        # In 8 unit steps this is 165 steps
        
        stepSize = 8
        
        testDev.setChannel(channel, 32112)
        
        time.sleep(0.5)
        
        trgDev.setPreCollectionSeq(0b111111)
        trgDev.setPreSeqExTime(3)
            
        for k in range(testRepeats):
            testDev.setChannel(channel, 32112+(k)*stepSize)
            time.sleep(0.5)
            
            trgDev.callPreSeq()

            val1 = acquire("CH1", rm.list_resources()[0])
            val2 = acquire("CH2", rm.list_resources()[0])
            
            testArray[:,3*k+0] = val1[0]
#            testArray[:,3*k+1] = np.ones_like(val1[1])*(k)*stepSize
            testArray[:,3*k+1] = 5*float(k*stepSize)/65535
            testArray[:,3*k+2] = val2[1]
    
    else:
        print('Incorrect test type')
    
    
    return testArray

def rgb(r, g, b):
    return [float(r)/255, float(g)/255, float(b)/255]

def plotTestArray(testArray, saveDest, returnHandle = False):
    trigColor = rgb(52, 152, 219)
    testColor = rgb(231, 76, 60)
    
    for k in range(testArray.shape[1]/3):
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
    
    
def startOscope():
    rm = pyvisa.ResourceManager()
    scope = rm.open_resource(rm.list_resources()[0])

    print(scope.query('*IDN?'))
    
    return scope, rm
    

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
    
    ser2 = octoDACDriver.octoDACStart('COM5', 115200, 1)
    
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
    
    testArray = deviceTest(n1, n2, testType, nTestRepeats, rm.list_resources()[0])
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    
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
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
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
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
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
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    #%% 
    # Jitter between triggering NicoLase out and test octoDAC, with sequences on all channels.
    # CH1 is trgDev output in pre-acquisition sequence
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
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
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
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
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
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
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
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
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
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
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
    nTestRepeats = 10
    
    channel = 'chan1_fast'
    
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0], channel = 1)
    plotTestArray(testArray, os.path.join('.\output', testType + '_' + channel + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '_' + channel + '.csv'), header = False)
    
    
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
    testArray = deviceTest(n1, o2, testType, nTestRepeats, rm.list_resources()[0])
    plotTestArray(testArray, os.path.join('.\output', testType + '.png'))
    dFrame = pd.DataFrame(testArray)
    dFrame.to_csv(os.path.join('.\output', testType + '.csv'), header = False)
    
    
    #%%
    ser1.close()
    ser2.close()

if __name__ == "__main__":
    main()