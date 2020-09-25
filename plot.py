import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import scipy.io
import argparse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

def getMat(filename):
    mat = scipy.io.loadmat(filename)
    return mat

def buildMean(val, temp):
    meanval = []
    meantemp = []
    temps = []
    index = 0

    for t in temp:
        if not t in temps:
            temps.append(t)

    for t in temps:      
        indices = [i for i, x in enumerate(temp) if x == t]
        mean = 0
        for i in indices:
            mean += val[i]
        mean /= indices.__len__()

        meantemp.append(t)
        meanval.append(mean)

        index += 1

    return (meanval, meantemp)


def meanArray(val, temp):
    mval = []
    mtemp = []

    for v, t in zip(val, temp):
        val, temp = buildMean(v, t)
        mval.append(val)
        mtemp.append(temp)

    return (mval, mtemp)

def plot_time(val, temp):
    fig, axs = plt.subplots(2,3)

    for i in range(3):
        axs[0, i].plot(range(len(val[i])), val[i],",")

    for i in range(3):
        axs[1, i].plot(range(len(temp[i])), temp[i],",")

    plt.show()

def plot_time_one_plt(val, temp, factor=[[1,1,1],[1,1,1]], offset=[[0,0,0],[0,0,0]], marker = None ,colors = ["red", "orange", "blue"]):
    fig, axs = plt.subplots(2)

    data = [val, temp]

    for j in range(2):
        for i in range(2):
            if (marker):
                t = pd.date_range(start=0, freq='100ms', periods=len(data[j][0]))
                if(len(data[j][0])>marker[i]['start']['index']):                  
                    axs[j].axvline(x=pd.to_datetime(t)[marker[i]['start']['index']], ymin=0, ymax=1, linestyle=':', color='green')
                if(len(data[j][0])>marker[i]['stop']['index']):   
                    axs[j].axvline(x=pd.to_datetime(t)[marker[i]['stop']['index']], ymin=0, ymax=1, linestyle=':', color='red')
        for i in range(3):
            t = pd.date_range(start=0, freq='100ms', periods=len(data[j][i]))
            axs[j].plot(pd.to_datetime(t), data[j][i],",", label='sensor_' + str(i) + "; offset: " + str(offset[j][i]) + "; factor: " + str(factor[j][i]), color=colors[i])
 

        
    axs[0].grid(True)
    axs[1].grid(True)
    axs[0].legend(prop={'size': 6})
    axs[1].legend(prop={'size': 6})

    axs[0].set_ylabel(r'$V$')
    axs[1].set_xlabel(r'$HH:MM:SS$')
    axs[1].set_ylabel(r'$°C$')

    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    
    fig.autofmt_xdate()
    plt.show()

def plot_norm_mean(val, temp):
    fig, axs = plt.subplots(2,3)

    for i in range(3):
        axs[0, i].plot(temp[i], val[i],",")

    val, temp = meanArray(val,temp)

    for i in range(3):
        axs[1, i].plot(temp[i], val[i],",")

    plt.show()

def filter(val, min, max):
    for i in range(3):
        val[i] = val[i][val[i]>min]
        val[i] = val[i][val[i]<max]

def compensate(list, marker, compensate_factor=True, compensate_offset = True):
    array = list
    factor = []
    offset = []

    mean, diff = calcMeanDiff(list, marker)

    for i in range(3):
        factor.append(diff[0] / diff[i])
        if(compensate_factor):
            array[i] *= factor[i]

    mean, diff = calcMeanDiff(array, marker)


    for i in range(3):
        offset.append(mean[0][0] - mean[i][0])
        if(compensate_offset):
            array[i] += offset[i]

        
    return (array, factor, offset)

def calcMeanDiff(list, marker):
    mean = [[],[],[]]
    diff = []
    for j in range(3):      
        for i in range(2):
            mean[j].append(np.mean(list[j][marker[i]['start']['index']:marker[i]['stop']['index']]))
        diff.append(mean[j][0] - mean[j][1])
    return (mean, diff)

# def norm_mlp(list, start=0, end=0):
#     arr = []
#     factor = []
#     arr_end = 0
#     if(end == 0):
#         arr_end = len(list[0])
#     else:
#         arr_end = end
#     mean = np.mean(list[0][start:arr_end])
#     for i in range(3):
#         if(end == 0):
#             arr_end = len(list[i])
#         else:
#             arr_end = end
#         factor.append(mean / np.mean(list[i][start:arr_end]))
#         arr.append(list[i] * factor[i])
#     return (arr, factor)

# def norm_add(list, start=0, end=0):
#     arr = []
#     offset = []
#     arr_end = []
#     if(end == 0):
#         arr_end = len(list[0])
#     else:
#         arr_end = end
#     mean = np.mean(list[0][start:arr_end])
#     for i in range(3):
#         offset.append(mean - np.mean(list[i][start:arr_end]))
#         arr.append(list[i] + offset[i])
#     return (arr, offset)

def extractMarker(arg_array):
    marker = []
    for i in range(len(arg_array)//2):
        marker.append(
            {
                'start' : {
                    'time': datetime.strptime(arg_array[i*2], '%H:%M:%S'),
                },
                'stop' : {
                    'time': datetime.strptime(arg_array[i*2+1], '%H:%M:%S'),
                }
            }
        )

    for m in marker:
        m['start']['seconds'] = (m['start']['time'] - datetime(1900, 1, 1)) / timedelta(seconds=1)
        m['stop']['seconds'] = (m['stop']['time'] - datetime(1900, 1, 1)) / timedelta(seconds=1)
        m['start']['index'] = int(m['start']['seconds'] * 10)
        m['stop']['index'] = int(m['stop']['seconds'] * 10)

    return marker

plot_type=['default','mean', 'time']

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('file', type=str, help='.mat filename', nargs=1)
parser.add_argument('-p', '--plot_type',dest='plot_type', type=str, nargs=1, choices=plot_type)
parser.add_argument('-c', '--compensate',dest='compensate', type=str, nargs=4, metavar=('marker_1_start', 'marker_1_stop', 'marker_2_start', 'marker_2_stop'))
parser.add_argument('-f', '--filter',dest='filter', action='store_const', const=True)
parser.add_argument('-s', '--slice',dest='slice', type=str, nargs=2, metavar=('start','stop'), help='Take a slice')
args = parser.parse_args()

data = getMat(args.file[0])

temp = [ data["channel4"][0], data["channel5"][0], data["channel6"][0]]
val = [ data["channel1"][0], data["channel2"][0], data["channel3"][0]]

val_offs = temp_offs = [1,1,1]
val_fact = temp_fact = [0,0,0]

marker = None

if(args.compensate):
    marker = extractMarker(args.compensate)

    val, val_fact, val_offs = compensate(val, marker)
    temp, temp_fact, temp_offs = compensate(temp, marker)

if(args.filter):
    # if(len(args.filter == 2)):
    #     filter(val, args.filter[0], args.filter[1])
    # else:
    filter(val, 0.65, 0.8)
    filter(temp, 5, 40)

if(args.slice):
    slice_marker = extractMarker(args.slice)[0]
    for i in range(3):
        val[i] = val[i][slice_marker['start']['index']:slice_marker['stop']['index']]
        temp[i] = temp[i][slice_marker['start']['index']:slice_marker['stop']['index']]

if(args.plot_type and args.plot_type[0] == 'mean'):
    plot_norm_mean(val,temp)
elif(args.plot_type and args.plot_type[0] == 'time'):
    plot_time(val,temp)
else:
    plot_time_one_plt(val, temp, [val_fact, temp_fact], [val_offs, temp_offs], marker)