#!/usr/bin/python3
import serial
import time
import argparse
import sys
import os
import calendar


def calcCrc( msg ):
        "Vypocet checksumu"
        crc = 0;
        for letter in msg:     # First Example
           crc = crc ^ ord(letter)
        crc = format(crc, 'X')
        return crc;

def makeCommand( msg ):
        "Vytvorenie vety"
        #final = b'$'+msg+'*'+calcCrc(msg)+'\n'
        veta = msg+'*'+calcCrc(msg)+'\n'
        final = b'$'+str.encode(veta)
        return final;

def getArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    parser.add_argument("--input")
    parser.add_argument("--output")
    args = parser.parse_args()
    output = args.output
    port = args.port
    args = args.input
    args = args.split(",")
    # args = [pair.replace(" ","") for pair in args]
    args_map = {}
    for arg in args:
       argument = arg.split(":")
       args_map[argument[0]] = argument[1]
    args_map["port"] = port
    args_map["output"] = output
    return args_map


def startReading(args):
    port = args["port"]
    ser = serial.Serial(port, 115200)
    readCmd = makeCommand('SGV')
    filePath = args["output"]
    now = calendar.timegm(time.gmtime())
    end = now + int(float(args["t_sim"]))
    readTimes = 0

    try:
        while (now < end):
            file = open(filePath, "a+")
            ser.write(makeCommand("SGV"))
            output = ser.readline()

            try :
                output = output.decode("utf-8")
                beginPos = output.find("$") + 1
                endPos = output.find("*")
                output = output[beginPos:endPos] + "\n"
                print(output)
            except ValueError:
                # How to handle such thing ?
                print("ops")

            file.write(output)
            now = calendar.timegm(time.gmtime())
            time.sleep(float(args["s_rate"])/1000.0);
            file.close()
            readTimes = readTimes + 1
        file.close()
        ser.close()
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)
        print("Could not create file")
        ser.close()
        sys.exit(0)

def stopDevice(args):
    ser = serial.Serial(args["port"], 115200)
    ser.write(makeCommand('SEE'))
    ser.close()

def app(args):
    ser = serial.Serial(args["port"], 115200)
    ser.write(makeCommand('SSE'))
    command = "SGV," + args["c_lamp"] + "," + args["c_fan"] + "," + args["c_led"]
    ser.write(makeCommand(command))
    ser.close()
    startReading(args)
    stopDevice(args)

if __name__ == '__main__':
    args = getArguments()
    app(args)
