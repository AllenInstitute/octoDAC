# -*- coding: utf-8 -*-
"""
Created on Mon May 18 11:04:45 2020

@author: Rusty Nicovich
"""

import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

from octoDACTestScript import rgb, plotTestArray

"""
Tests to quantify:

digitalJitter
analogJitter
tophatJitter
analogCycleJitter
analogJitterAllChannels
topHatJitterAllChannels
topHatJitterAllChansLonger
waveformNaive
waveformCorrected
linearity
stepResolution
"""

basePath = r"C:\Users\rusty\Documents\octoDAC\octodac\code\Python\octoDAC\validation\output"

writeFile = "octoDACanalysisResults.txt"

fID = open(os.path.join(basePath, writeFile), 'w+')
fID.write('octoDAC analysis results\n')

#%%
# -----------------------------------------
# digitalJitter
# Measure time from trigger to test
readFile = os.path.join(basePath, 'digitalJitterCH1.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

deltaT = np.zeros((int(data.shape[1]/3), 1))
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    trigT = t[np.argmax(trig > 2.5)]
    sigT = t[np.argmax(sig > 2.5)]
    
    deltaT[k] = sigT - trigT

fID.write('-----------------\n')
fID.write('Digital jitter\n')
fID.write('Delay between input trigger and output digital signal\n')
fID.write('File : {}\n'.format(readFile))
fID.write('Result : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaT), np.std(deltaT)))

#%%
# -----------------------------------------
# analogJitter
# Measure time from trigger to test
readFile = os.path.join(basePath, 'analogJitter.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

deltaT = np.zeros((int(data.shape[1]/3), 1))
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    trigT = t[np.amin(np.where(trig > 2.5))]
    sigT = t[np.amin(np.where(sig > 2.5))]
    
    deltaT[k] = sigT - trigT

fID.write('-----------------\n')
fID.write('Analog jitter\n')
fID.write('Delay between input trigger and output analog signal\n')
fID.write('File : {}\n'.format(readFile))
fID.write('Result : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaT), np.std(deltaT)))

#%%

# -----------------------------------------
# tophatJitter
# Measure time from rise to fall of top hat, minus expected time
readFile = os.path.join(basePath, 'tophatJitter.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

expectedValue = 100e-6 # seconds
deltaT = np.zeros((int(data.shape[1]/3), 1))
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    trigT = t[np.amin(np.where(sig > 2.5))]
    sigT = t[np.amax(np.where(sig > 2.5))]
    
    deltaT[k] = sigT - trigT - expectedValue

fID.write('-----------------\n')
fID.write('Top hat jitter\n')
fID.write('Jitter between expected drop of 100 µs top hat and measured\n')
fID.write('File : {}\n'.format(readFile))
fID.write('Result : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaT), np.std(deltaT)))

#%% analogCycleJitter
# Measure time of drop to next rise in a high-low-high pulse
readFile = os.path.join(basePath, 'analogCycleJitter.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

expectedValue = 100e-6 # seconds
deltaT = np.zeros((int(data.shape[1]/3), 1))
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    trigT = t[np.amin(np.where(sig < 2.5))]
    sigT = t[np.amax(np.where(sig < 2.5))]
    
    deltaT[k] = sigT - trigT - expectedValue

fID.write('-----------------\n')
fID.write('Analog cycle jitter\n')
fID.write('Jitter between expected rise of low value in 100 µs square pulse and measured\n')
fID.write('File : {}\n'.format(readFile))
fID.write('Result : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaT), np.std(deltaT)))

#%% analogJitterAllChannels
# Measure time of drop to next rise
readFile = os.path.join(basePath, 'analogJitterAllChannels.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

deltaTFirst = np.zeros((int(data.shape[1]/3), 1))
deltaTLast = np.zeros((int(data.shape[1]/3), 1))
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    trigT = t[np.amin(np.where(trig > 2.5))]
    sigT = t[np.amin(np.where(sig > 2.5))]
    
    deltaTFirst[k] = sigT
    deltaTLast[k] = trigT

fID.write('-----------------\n')
fID.write('Analog  jitter all channels\n')
fID.write('Trigger at t = 0.  Rise time for first and last channels when all channels have t = 0 sequence entry.\n')
fID.write('File : {}\n'.format(readFile))
fID.write('Result first channel : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTFirst), np.std(deltaTFirst)))
fID.write('Result last channel : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTLast), np.std(deltaTLast)))

#%% topHatJitterAllChannels
# Measure time of rise to next drop, but with multiple channels in sequence
readFile = os.path.join(basePath, 'topHatJitterAllChannels.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

expectedT = 100e-6;
deltaTFirst = np.zeros((int(data.shape[1]/3), 1))
deltaTLast = np.zeros((int(data.shape[1]/3), 1))
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    trigT = t[np.amin(np.where(trig > 2.5))]
    sigT = t[np.amax(np.where(trig > 2.5))]
    
    deltaTFirst[k] = sigT - trigT - expectedT
    
    trigT = t[np.amin(np.where(sig > 2.5))]
    sigT = t[np.amax(np.where(sig > 2.5))]
    
    deltaTLast[k] = sigT - trigT - expectedT

fID.write('-----------------\n')
fID.write('Top hat jitter all channels\n')
fID.write('Trigger at t = 0, 100 µs top hat.  Rise time for first and last channels when all channels have t = 0 sequence entry.\n')
fID.write('File : {}\n'.format(readFile))
fID.write('Result first channel : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTFirst), np.std(deltaTFirst)))
fID.write('Result last channel : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTLast), np.std(deltaTLast)))

#%% topHatJitterAllChannelsLonger
# Measure time of rise to next drop, but with multiple channels in sequence
readFile = os.path.join(basePath, 'topHatJitterAllChansLonger.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

expectedT = 500e-6;
deltaTFirst = np.zeros((int(data.shape[1]/3), 1))
deltaTLast = np.zeros((int(data.shape[1]/3), 1))
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    trigT = t[np.amin(np.where(trig > 2.5))]
    sigT = t[np.amax(np.where(trig > 2.5))]
    
    deltaTFirst[k] = sigT - trigT - expectedT
    
    trigT = t[np.amin(np.where(sig > 2.5))]
    sigT = t[np.amax(np.where(sig > 2.5))]
    
    deltaTLast[k] = sigT - trigT - expectedT

fID.write('-----------------\n')
fID.write('Top hat jitter all channels, longer\n')
fID.write('Trigger at t = 0, 500 µs top hat.  Rise time for first and last channels when all channels have t = 0 sequence entry.\n')
fID.write('File : {}\n'.format(readFile))
fID.write('Result first channel : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTFirst), np.std(deltaTFirst)))
fID.write('Result last channel : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTLast), np.std(deltaTLast)))



#%% waveformNaive
# Period/frequency of a cycle that should be 2.5 kHz
# Measure value from first rise after t = 0 to next rise
readFile = os.path.join(basePath, 'waveformNaive.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

expectedValues = 200e-6
deltaTHigh = []
deltaTLow = []
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    risingEdges = []
    fallingEdges = []
    for p in range(int(data.shape[0]-1)):
        
        if (sig[p] < 2.5) and (sig[p+1] > 2.5):
            risingEdges.append(p)
            
        if (sig[p] > 2.5) and (sig[p+1] < 2.5):
            fallingEdges.append(p)
    
    # Starts with a falling edge
    for p in risingEdges:
        fallsLater = [x for x in fallingEdges if x > p]
        
        if len(fallsLater) > 0:
            nextFall = np.amin(fallsLater)
        
            peakTime = t[nextFall] - t[p] - expectedValues
            
            deltaTHigh.append(peakTime)
            
    for p in fallingEdges:
        risesLater = [x for x in risingEdges if x > p]
        
        if len(risesLater) > 0:
            nextRise = np.amin(risesLater)
        
            peakTime = t[nextRise] - t[p] - expectedValues
            
            deltaTLow.append(peakTime)
            
fID.write('-----------------\n')
fID.write('Waveform timing with naive input\n')
fID.write('Trigger at t = 0 on rising edge.  Should be a 2.5 kHz square wave with 50% duty cycle.  200 µs on both high and low values.\n')
fID.write('File : {}\n'.format(readFile))
fID.write('High value period : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTHigh), np.std(deltaTHigh)))
fID.write('Low value period : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTLow), np.std(deltaTLow)))

#%% waveformCorrected
# Period/frequency of a cycle that should be 2.5 kHz
# Measure value from first rise after t = 0 to next rise
readFile = os.path.join(basePath, 'waveformCorrected.csv')
data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
#hand = plotTestArray(data, 'test.png', returnHandle = True)

expectedValues = 200e-6
deltaTHigh = []
deltaTLow = []
# Measure trigger-signal deltaT value
for k in range(int(data.shape[1]/3)):
    t = data[:,3*k+0]
    trig = data[:,3*k+1]
    sig = data[:,3*k+2]
    
    risingEdges = []
    fallingEdges = []
    for p in range(int(data.shape[0]-1)):
        
        if (sig[p] < 2.5) and (sig[p+1] > 2.5):
            risingEdges.append(p)
            
        if (sig[p] > 2.5) and (sig[p+1] < 2.5):
            fallingEdges.append(p)
    
    # Starts with a falling edge
    for p in risingEdges:
        fallsLater = [x for x in fallingEdges if x > p]
        
        if len(fallsLater) > 0:
            nextFall = np.amin(fallsLater)
        
            peakTime = t[nextFall] - t[p] - expectedValues
            
            deltaTHigh.append(peakTime)
            
    for p in fallingEdges:
        risesLater = [x for x in risingEdges if x > p]
        
        if len(risesLater) > 0:
            nextRise = np.amin(risesLater)
        
            peakTime = t[nextRise] - t[p] - expectedValues
            
            deltaTLow.append(peakTime)
            
fID.write('-----------------\n')
fID.write('Waveform timing with corrected input\n')
fID.write('Trigger at t = 0 on rising edge.  Should be a 2.5 kHz square wave with 50% duty cycle.  200 µs on both high and low values.\n')
fID.write('File : {}\n'.format(readFile))
fID.write('High value period : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTHigh), np.std(deltaTHigh)))
fID.write('Low value period : {} +- {} (mean +- stddev)\n'.format(np.mean(deltaTLow), np.std(deltaTLow)))

#%% linearity

fID.write('-----------------\n')
fID.write('Linearity measurements\n')
fID.write('Set value, measure for 250 ms.  Plot mean + std dev at each value.\n')

fList = list()


# fileList = ['linearity_chan1.csv',
#             'linearity_chan2.csv',
#             'linearity_chan3.csv',
#             'linearity_chan4.csv',
#             'linearity_chan5.csv',
#             'linearity_chan6.csv',
#             'linearity_chan7.csv',
#             'linearity_chan8.csv']

# fList.append(fileList)


# fileList = ['linearity_chan1_Vin.csv',
#             'linearity_chan2_Vin.csv',
#             'linearity_chan3_Vin.csv',
#             'linearity_chan4_Vin.csv',
#             'linearity_chan5_Vin.csv',
#             'linearity_chan6_Vin.csv',
#             'linearity_chan7_Vin.csv',
#             'linearity_chan8_Vin.csv']

# fList.append(fileList)

fileList = ['linearity_chan1.csv',
            'linearity_chan8.csv']

fList.append(fileList)


fileList = ['linearity_chan1_Vin.csv',
            'linearity_chan8_Vin.csv']

fList.append(fileList)

colorList = [rgb(52, 152, 219),
             rgb(26, 188, 156), 
             rgb(46, 204, 113), 
             rgb(155, 89, 182), 
             rgb(241, 196, 15), 
             rgb(230, 126, 34),
             rgb(231, 76, 60),
             rgb(192, 57, 43)]


for fL, fileList in enumerate(fList):

    linPlot = plt.figure()
    print(fileList)
    
    
    lineFits = []
    
    
    
    for i, f in enumerate(fileList):
        readFile = os.path.join(basePath, f)
        data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
        
        plotVals = np.zeros((int(data.shape[1]/3), 3))
        
        for k in range(int(data.shape[1]/3)):
            t = data[:,3*k+0]
            trig = data[:,3*k+1]
            sig = data[:,3*k+2]
            
            plotVals[k,0] = np.mean(trig)
            plotVals[k,1] = np.mean(sig)
            plotVals[k,2] = np.std(sig)
            
        # Fit to a line
        z = np.polyfit(plotVals[:,0], plotVals[:,1], 1)
        lineFits.append(z)
        p = np.poly1d(z)
        xp = np.linspace(0, 5, 10)
        
        plt.errorbar(plotVals[:,0], plotVals[:,1], yerr = plotVals[:,2], fmt = '.', 
                     color = colorList[i], markersize = 4)
        plt.plot(xp, p(xp), color = colorList[i])
        
        fID.write('File : {}\n'.format(readFile))
        fID.write('Line fits : {}, {} (slope, offset)\n'.format(z[0], z[1]))
            
    plt.plot([0, 5], [0, 5], color = rgb(52, 73, 94))
    plt.show()
    plt.xlabel('Set value (V)')
    plt.ylabel('Measured value (V)')
    
    figPath = 'linearityPlots.png'
    if fL == 1:
        figPath = 'linearityPlots_Vin.png'
    
    plt.savefig(os.path.join(basePath, figPath), bbox_inches='tight', dpi = 300)

#%% Fast time ripple

# Measure AC voltage ripple at 10 set values, 5 ms window


fList = list()
fileList = ['linearity_chan1_fast.csv',
            'linearity_chan8_fast.csv']
fList.append(fileList)

# fileList = ['linearity_chan1_Vin_fast.csv', 
#             'linearity_chan8_Vin_fast.csv']

# fList.append(fileList)


colorList = [rgb(52, 152, 219),
             rgb(192, 57, 43)]

for fL, fileList in enumerate(fList):
    
    print(fileList)

    plt.figure()
    for i, f in enumerate(fileList):
        readFile = os.path.join(basePath, f)
        data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
        
        plotVals = np.zeros((int(data.shape[1]/3), 3))
        
        for k in range(int(data.shape[1]/3)):
            t = data[:,3*k+0]
            trig = data[:,3*k+1]
            sig = data[:,3*k+2]
            
            plt.errorbar(np.mean(trig), np.mean(sig), yerr = np.std(sig), fmt = '.', 
                         color = colorList[i], markersize = 8)
            
    plt.plot([0, 5], [0, 0], color = rgb(149, 165, 166), linestyle = ':')
    plt.show()
    plt.xlabel('Set value (V)')
    plt.ylabel('AC ripple (V)') 
    
    if fL == 0:
        saveName = 'acRippleSummary.png'
    elif fL == 1:
        saveName = 'acRippleSummary_Vin.png'
    
    plt.savefig(os.path.join(basePath, saveName), bbox_inches='tight', dpi = 300)
    
    # Plot example of chan8 ripple at 1V, 5V
    f = fileList[-1]
    readFile = os.path.join(basePath, f)
    data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
    
    plotVals = np.zeros((int(data.shape[1]/3), 3))
    
    plt.figure()
    for k in range(int(data.shape[1]/3)):
        t = data[:,3*k+0]
        trig = data[:,3*k+1]
        sig = data[:,3*k+2]
        
        if (np.abs(trig[0] - 0.5) < 0.1):
            print('1')
            legHand1 = plt.plot(t, sig, color = rgb(231, 76, 60), zorder = 1, label = '0.54V')
            
        elif (np.abs(trig[0] - 4.4) < 0.05):
            print('5')
            legHand8 = plt.plot(t, sig, color = rgb(192, 57, 43), zorder = 0, label = '4.44V')
            
    plt.legend()
    plt.xlabel('time (sec)')
    plt.ylabel('AC ripple (V)')
    
    if fL == 0:
        saveName = 'acRippleChan8.png'
    elif fL == 1:
        saveName = 'acRippleChan8_Vin.png'
            
    plt.savefig(os.path.join(basePath, saveName), bbox_inches='tight', dpi = 300) 
     
#%% stepResolution

# fileList = ['stepResolution.csv', 
#             'stepResolution_Vin.csv']

fileList = ['stepResolution.csv']

for fL in fileList:
    
    print(fL)

    # DC value w/ small steps
    plt.figure()
    readFile = os.path.join(basePath, fL)
    data = pd.read_csv(readFile, header = None).to_numpy()[:,1:]
    
    plotVals = np.zeros((int(data.shape[1]/3), 3))
    
    stdDevList = []
    
    for k in range(int(data.shape[1]/3)):
        t = data[:,3*k+0]
        trig = data[:,3*k+1] + (5*(3276)/65535) # Recorded as test value above offset.  Need to add offset back in + rescale
        sig = data[:,3*k+2]
        
        plt.errorbar(np.mean(trig), np.mean(sig), yerr = np.std(sig), fmt = '.', 
                     color = rgb(52, 152, 219), markersize = 4)
        
        stdDevList.append(np.std(sig))
    
    
    if fL.endswith('Vin.csv'):
        saveName = 'stepResolutionSummary_Vin.png'
    else:
        saveName = 'stepResolutionSummary.png'
        
    plt.show()
    plt.xlabel('Set value (V)')
    plt.ylabel('Measured value (V)')  
    plt.savefig(os.path.join(basePath, saveName), bbox_inches='tight', dpi = 300) 
    
    fID.write('-----------------\n')
    fID.write('stepResolution\n')
    fID.write('0.1 sec window.  Small steps around 0.25V.\n')
    fID.write('File : {}\n'.format(readFile))
    fID.write('Mean deviation : {}\n'.format(np.mean(stdDevList)))


#%%
fID.close()