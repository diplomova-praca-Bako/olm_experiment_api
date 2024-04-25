#!/usr/bin/python3

import argparse
import os
import serial
import time
import math
import random
from multiprocessing import Process
import re

arduino = None
cube_size=8


def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time} seconds")
        return result
    return wrapper

@time_it
def wait_for_acknowledgement():
    global arduino
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode().strip()
            if line == "ACK":
                break

@time_it
def getArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    parser.add_argument("--input")
    parser.add_argument("--output")
    args = parser.parse_args()

    print("ARGS getArguments")
    print(args)

    input_str = args.input
    # keys = ['c_code', 'uploaded_code_file', 'uploaded_file', 'demo_name']
    keys = ['python_code', 'uploaded_code_file', 'uploaded_file', 'demo_name']
    result = {}

    pattern = re.compile(r'(' + '|'.join(keys) + r'):(.*?)(?=(?:, ' + '|'.join(keys) + r':)|$)', re.DOTALL)

    matches = pattern.finditer(input_str)
    for match in matches:
        key = match.group(1)
        value = match.group(2).strip().rstrip(',')
        result[key] = value

    # Add the port and output which are parsed directly from the arguments
    result['port'] = args.port
    result['output'] = args.output

    return result

def main():
    args=getArguments()

    if(args["demo_name"] and args["demo_name"] != ""):
        demo_file_path = os.path.join(args['uploaded_file'], args['demo_name'] + '.py')
        demo_content: any
        try:
            with open(demo_file_path, 'r') as file:
                demo_content = file.read()
        except FileNotFoundError:
            print(f"File '{demo_file_path}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        run_process(demo_content, args["port"])

    elif(args["uploaded_code_file"] and args["uploaded_code_file"] != ""):
        run_process(args["uploaded_code_file"], args["port"])
    else:
        run_process(args["python_code"], args["port"])


def run_process(code, port):
    code_process = Process(target=run_instructions, args=(code,port))
    code_process.start()

    code_process.join(timeout=12.5)
    if code_process.is_alive():
        print("Timeout reached. Terminating process now...")
        code_process.terminate()
        code_process.join()

        arduinoClear = serial.Serial(port, 250000)
        arduinoClear.write(b"clearCube\n")
        arduinoClear.close()
    print("Process has been terminated.")
#    arduino.close()

def run_instructions(code, port):
    global arduino
    arduino = serial.Serial(port, 250000)
    time.sleep(2) #inicializacia arduina

    local_scope = {
        'setPixelColor': setPixelColor,
        'setMultiplePixelColor': setMultiplePixelColor,
        'clearCube': clearCube,
        'cube_size': cube_size,
        'arduino': arduino,
        # 'time': time,
        'sleep': sleep,
        'math': math,
        'random': random
    }

    try:
        print(repr(code))
        exec(code, local_scope)
    except Exception as e:
        print(f"Error executing threaded dynamic code: {e}")
    finally:
        clearCube()
        arduino.close()


@time_it
def setPixelColor(position, color):
    index = xyz_to_index(position[0], position[1], position[2])
    if len(color) != 3:
        raise ValueError("Color must be a list of three integers")

    command = f"Pixel,{color[0]},{color[1]},{color[2]},{index}\n"
    arduino.write(command.encode())
    wait_for_acknowledgement()  # Wait for ACK instead of using sleep

@time_it
def setMultiplePixelColor(positions, color):
    if len(color) != 3:
        raise ValueError("Color must be a list of three integers")

    # Convert positions to a list of indexes
    indexes = [xyz_to_index(pos[0], pos[1], pos[2]) for pos in positions]
    
    command = f"Pixels,{color[0]},{color[1]},{color[2]},"
    for index in indexes:
        command += f"{index},"
    command += f"\n"

    arduino.write(command.encode())
    wait_for_acknowledgement()

@time_it
def clearCube():
    global arduino
    arduino.write(b"clearCube\n")
    wait_for_acknowledgement()

@time_it
def sleep(millis):
    global arduino
    command = f"sleep,{millis}\n"
    arduino.write(command.encode())
    wait_for_acknowledgement()


# def sleep(millis):
#     time.sleep(millis/1000)

def xyz_to_index(x, y, z):
    # return y + z * cube_size + x * cube_size * cube_size
    return z * cube_size * cube_size + x * cube_size + y

if __name__ == '__main__':
    main()
