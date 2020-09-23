import matplotlib.pyplot as plt
import scipy.io
import argparse
import pandas as pd
import numpy as np

def getMat(filename):
    mat = scipy.io.loadmat(filename)
    return mat

def getData(filename):

    count = 0

    val = [[],[],[]]
    temp = [[],[],[]]

    with open(filename) as fp: 
        while True: 
            for i in range(0, 3):
                v = float(fp.readline()[:-2])
                val[i].append(v)
                count += 1
            for i in range(0, 3):
                v = float(fp.readline()[:-2])
                temp[i].append(v)
                count += 1
            count += 1
            separator = fp.readline()[:-1]
            if not separator:
                break
            if separator != '----': 
                print("ERROR IN FILE")

    return (val, temp)

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

def plot_time_one_plt(val, temp, factor=[[0,0,0],[0,0,0]], offset=[[0,0,0],[0,0,0]]):
    fig, axs = plt.subplots(2)

    start = pd.Timestamp('2015-07-01')
    end = pd.Timestamp('2015-08-01')
    t = np.linspace(start.value, end.value, 100)
    t = pd.to_datetime(t)

    data = [val, temp]

    for j in range(2):
        for i in range(3):
            axs[j].plot(range(len(data[j][i])), data[j][i],",", label='sensor_' + str(i) + "; offset: " + str(offset[j][i]) + "; factor: " + str(factor[j][i]))

    axs[0].grid(True)
    axs[1].grid(True)
    axs[0].legend(prop={'size': 6})
    axs[1].legend(prop={'size': 6})

    axs[0].set_xlabel(r'$steps$')
    axs[0].set_ylabel(r'$V$')
    axs[1].set_xlabel(r'$steps$')
    axs[1].set_ylabel(r'$°C$')

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

def norm_mlp(list):
    arr = []
    factor = []
    mean = np.mean(list[0])
    for i in range(3):
        factor.append(mean / np.mean(list[i]))
        arr.append(list[i] * factor[i])
    return (arr, factor)

def norm_add(list):
    arr = []
    offset = []
    mean = np.mean(list[0])
    for i in range(3):
        offset.append(mean - np.mean(list[i]))
        arr.append(list[i] + offset[i])
    return (arr, offset)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('file', type=str, help='.mat filename', nargs=1)
parser.add_argument('-p' '--plot_type',dest='plot_type', type=str, nargs=1)
parser.add_argument('-c' '--compensate',dest='compensate', type=bool, nargs=1)
parser.add_argument('-f' '--filter',dest='filter', type=bool, nargs=1)
args = parser.parse_args()

data = getMat(args.file[0])

temp = [ data["channel4"][0], data["channel5"][0], data["channel6"][0]]
val = [ data["channel1"][0], data["channel2"][0], data["channel3"][0]]

val_offs = temp_offs = [1,1,1]
val_fact = temp_fact = [0,0,0]

if(args.filter):
    filter(val, 0.2, 1)
    filter(temp, 5, 40)

if(args.compensate):
    val, val_offs = norm_add(val)
    temp, temp_offs = norm_add(temp)

    val, val_fact = norm_mlp(val)
    temp, temp_fact = norm_mlp(temp)

if(args.plot_type and args.plot_type[0] == 'mean'):
    plot_norm_mean(val,temp)
elif(args.plot_type and args.plot_type[0] == 'one'):
    plot_time_one_plt(val, temp, [val_fact, temp_fact], [val_offs, temp_offs])
else:
    plot_time(val,temp)

'''
val, temp = getData("cool.txt")

#val, temp = meanArray(val,temp)

axs[0,0].plot(data["channel4"][0], data["channel1"][0],"x")
axs[0,1].plot(data["channel5"][0], data["channel2"][0],"x")
axs[0,2].plot(data["channel6"][0], data["channel3"][0],"x")

fig, axs = plt.subplots(3, 3)
axs[0, 0].plot(temp[0], val[0],"x")
axs[0, 1].plot(temp[1], val[1],"x")
axs[0, 2].plot(temp[2], val[2],"x")

val, temp = getData("heat.txt")

#val, temp = meanArray(val,temp)

axs[1, 0].plot(temp[0], val[0],"x")
axs[1, 1].plot(temp[1], val[1],"x")
axs[1, 2].plot(temp[2], val[2],"x")



val, temp = getData("temper.txt")

#val, temp = meanArray(val,temp)

axs[2, 0].plot(temp[0], val[0],"x")
axs[2, 1].plot(temp[1], val[1],"x")
axs[2, 2].plot(temp[2], val[2],"x")


plt.show()
'''