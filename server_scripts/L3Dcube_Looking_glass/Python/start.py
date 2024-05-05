#!/usr/bin/python3

import argparse
import os
import serial
import time
import math
import random
from multiprocessing import Process, Manager
import re
import sys
import tempfile


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
    elif(args["python_code"] and args["python_code"] != ""):
        run_process(args["python_code"], args["port"])
    else:
        return

def getArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    parser.add_argument("--input")
    parser.add_argument("--output")
    args = parser.parse_args()

    input_str = args.input
    keys = ['python_code', 'uploaded_code_file', 'uploaded_file', 'demo_name']
    result = {}
    pattern = re.compile(r'(' + '|'.join(keys) + r'):(.*?)(?=(?:, ' + '|'.join(keys) + r':)|$)', re.DOTALL)
    matches = pattern.finditer(input_str)
    for match in matches:
        key = match.group(1)
        value = match.group(2).strip().rstrip(',')
        result[key] = value

    result['port'] = args.port
    result['output'] = args.output
    return result

def process_wrapper(shared_dict, code, temp_file_path):
    output = generate_arduino_instructions(code, temp_file_path)
    shared_dict['output'] = output
    
def run_process(code, port):
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = temp_file.name

    with Manager() as manager:
        shared_dict = manager.dict()

        code_process = Process(target=process_wrapper, args=(shared_dict, code, temp_file_path))
        code_process.start()
        code_process.join(timeout=0.1)

        if code_process.is_alive():
            print("Timeout reached. Terminating process now...")
            code_process.terminate()
            code_process.join()

    try:
        with open(temp_file_path, 'r') as file:
            output = file.read()
            instructions = output.split('\n')
    
            send_serial_instructions_process = Process(target=send_serial_instructions, args=(port, instructions))
            send_serial_instructions_process.start()

            send_serial_instructions_process.join(timeout=30)
            if send_serial_instructions_process.is_alive():
                print("Timeout reached. Terminating process now...")
                send_serial_instructions_process.terminate()
                send_serial_instructions_process.join()

                arduinoClear = serial.Serial(port, 250000)
                arduinoClear.write(b"clearCube\n")
                arduinoClear.close()

            print("Process has been terminated.")

    except IOError:
        print("Failed to read output from the temporary file.")

        os.remove(temp_file_path)
        print("Process has been terminated.")

def generate_arduino_instructions(code, temp_file_path):
    local_scope = {
        'setLed': setLed,
        'clearLed': clearLed,
        'setLeds': setLeds,
        'clearCube': clearCube,
        'sleep': sleep,
        'math': math,
        'random': random
    }

    with open(temp_file_path, "w") as temp_file:
        old_stdout = sys.stdout
        sys.stdout = temp_file

        try:
            exec(code, local_scope)
        except Exception as e:
            print(f"Error executing dynamic code: {e}")
            raise(e)

        sys.stdout = old_stdout

def send_serial_instructions(port, instructions):

    # arduino_init_start = time.time()

    arduino = serial.Serial(port, 250000)
    wait_for_acknowledgement(arduino)  #this instead of time.sleep(2)

    # arduino_end_time = time.time()
    # arduino_duration = arduino_end_time - arduino_init_start
    # print(f"Arduino connection established in {arduino_duration} seconds")

    #time.sleep(2)


    for instruction in instructions:
        # instruction_start_time = time.time()

        # print(f"Sending instruction to Arduino: {instruction}")
        
        arduino.write((instruction + '\n').encode())
        
        wait_for_acknowledgement(arduino)
        # instruction_end_time = time.time()
        # instruction_duration = instruction_end_time - instruction_start_time
        # print(f"instruction executed in {instruction_duration} seconds")

    arduino.write(b"clearCube\n")

    if arduino:
        arduino.close()

def wait_for_acknowledgement(arduino):
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode().strip()
            if line == "ACK":
                # print("ACK received")
                break

def setLed(position, color):
    index = xyz_to_index(position[0], position[1], position[2])
    instruction = f"Pixel,{color[0]},{color[1]},{color[2]},{index}"
    print(instruction)

def clearLed(position):
    index = xyz_to_index(position[0], position[1], position[2])
    instruction = f"ClPixel,{index}"
    print(instruction)

def setLeds(positions, color):
    indexes = [xyz_to_index(pos[0], pos[1], pos[2]) for pos in positions]
    instruction = f"Pixels,{color[0]},{color[1]},{color[2]},"
    instruction += ",".join(map(str, indexes))
    print(instruction)

def clearCube():
    print("clearCube\n")

def sleep(millis):
    print(f"sleep,{millis}")

def xyz_to_index(x, y, z):
    return z * 8 * 8 + x * 8 + y

if __name__ == '__main__':
    main()
