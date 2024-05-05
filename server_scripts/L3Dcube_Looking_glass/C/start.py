#!/usr/bin/python3

import argparse
import subprocess
import os
import serial
import time
import tempfile
import re
from multiprocessing import Process


def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time} seconds")
        return result
    return wrapper

def wait_for_acknowledgement(arduino):
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode().strip()
            if line == "ACK":
                print("ACK received")
                break


def getArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    parser.add_argument("--input")
    parser.add_argument("--output")
    args = parser.parse_args()

    print("ARGS getArguments")
    print(args)

    input_str = args.input
    keys = ['c_code', 'uploaded_code_file', 'uploaded_file', 'demo_name']
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


def create_cpp_file_from_template(cpp_code):
    cpp_template = """
#include<iostream>
#include<chrono>
#include<thread>
#include<vector>

const int cube_size = 8;

using namespace std;


namespace SafeAPI {{

    int xyzToIndex(int x, int y, int z) {{
        return z * cube_size * cube_size + x * cube_size + y;
    }}

    void setLed(std::vector<int> position, std::vector<int> color) {{

        int index = xyzToIndex(position[0], position[1], position[2]);
        int r = color[0];
        int g = color[1];
        int b = color[2];

        cout << "Pixel," << r << "," << g << "," << b << "," << index << endl;
    }}

    void setLeds(std::vector<std::vector<int>> positions, std::vector<int> color) {{
        int r = color[0];
        int g = color[1];
        int b = color[2];

        cout << "Pixels," << r << "," << g << "," << b;

        std::vector<int> indexes;

        for (size_t i = 0; i < positions.size(); ++i) {{
            if (positions[i].size() == 3) {{ 
                int index = xyzToIndex(positions[i][0], positions[i][1], positions[i][2]);
                indexes.push_back(index);
                cout << "," << index;
            }}
        }}

        cout << endl;
    }}

    void clearCube() {{
    cout << "clearCube" << endl;
    }}

    void sleep(int millis) {{
        cout << "sleep" << "," << millis << endl;

    }}
}}

int main() {{
    using namespace SafeAPI;

    {cpp_code}
    return 0;
}}
"""

    cpp_content = cpp_template.format(cpp_code=cpp_code)

    temp_cpp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".cpp")
    with open(temp_cpp_file.name, 'w') as file:
        file.write(cpp_content)
    
    return temp_cpp_file.name


def main():
  args = getArguments()
  if(args["demo_name"] and args["demo_name"] != ""):
    demo_file_path = os.path.join(args['uploaded_file'], args['demo_name'] + '.c')
    demo_content: any
    try:
        with open(demo_file_path, 'r') as file:
            demo_content = file.read()
    except FileNotFoundError:
        print(f"File '{demo_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
    run_instructions(demo_content, args["port"])

  elif(args["uploaded_code_file"] and args["uploaded_code_file"] != ""):
    run_instructions(args["uploaded_code_file"], args["port"])
  else:
    run_instructions(args["c_code"], args["port"])


def run_instructions(code, port):
  cpp_file_path = create_cpp_file_from_template(code)
  command_outputs = compile_and_run_cpp(cpp_file_path)
  if command_outputs:

    commands = command_outputs.split('\n')
    send_serial_commands_process = Process(target=send_serial_commands, args=(port, commands))
    send_serial_commands_process.start()

    send_serial_commands_process.join(timeout=30)
    if send_serial_commands_process.is_alive():
        print("Timeout reached. Terminating process now...")
        send_serial_commands_process.terminate()
        send_serial_commands_process.join()
        arduinoClear = serial.Serial(port, 250000)
        arduinoClear.write(b"clearCube\n")
        arduinoClear.close()

# Function to compile and run C++ code, with timeout handling
def compile_and_run_cpp(cpp_file_path):
    executable_path = cpp_file_path.rsplit('.', 1)[0]
    compile_command = f"g++ -std=c++11 {cpp_file_path} -o {executable_path}"
    output = ""
    try:
        # Compiling the C++ code
        subprocess.check_call(compile_command, shell=True)
        print("Compilation successful.")

        # Attempt to run the executable with a timeout
        process = subprocess.Popen([executable_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            output, errors = process.communicate(timeout=0.5)
        except subprocess.TimeoutExpired:
            process.kill()
            output, errors = process.communicate()
            print(f"Process timed out. Partial output: {output.strip()}")
        return output.strip()

    except subprocess.CalledProcessError as e:
        print(f"Error during compilation or execution: {e}")
    finally:
        # Cleanup
        os.remove(cpp_file_path)
        if os.path.exists(executable_path):
            os.remove(executable_path)
    return output



def send_serial_commands(port, commands):
    arduino = serial.Serial(port, 250000)
    wait_for_acknowledgement(arduino)  #this instead of time.sleep(2)


    for command in commands:
        arduino.write((command + '\n').encode())
        
        wait_for_acknowledgement(arduino)

    arduino.write(b"clearCube\n")

    if arduino:
        arduino.close()



if __name__ == '__main__':
    main()
