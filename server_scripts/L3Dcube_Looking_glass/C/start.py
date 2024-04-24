#!/usr/bin/python3

import argparse
import subprocess
import os
import serial
import time
import tempfile
import re

arduino = None

def time_it(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} executed in {end_time - start_time} seconds")
        return result
    return wrapper

def wait_for_acknowledgement():
    global arduino
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
    # keys = ['c_code', 'uploaded_code_file', 'uploaded_file', 'demo_name']
    keys = ['c_code', 'uploaded_code_file', 'uploaded_file', 'file_name']
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


int xyzToIndex(int x, int y, int z) {{
    return z * cube_size * cube_size + x * cube_size + y;
}}

void setPixelColor(std::vector<int> position, std::vector<int> color) {{

    int index = xyzToIndex(position[0], position[1], position[2]);
    int r = color[0];
    int g = color[1];
    int b = color[2];

    cout << "Pixel," << r << "," << g << "," << b << "," << index << endl;
}}

void setMultiplePixelColor(std::vector<std::vector<int>> positions, std::vector<int> color) {{
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

int main() {{
    {cpp_code}
    return 0;
}}
"""
    # Fill the template with the user-provided C++ code
    # The double curly braces {{ and }} are escaped and treated as literal curly braces in the formatted string
    cpp_content = cpp_template.format(cpp_code=cpp_code)

    # Create a temporary file to hold the C++ code
    temp_cpp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".cpp")
    with open(temp_cpp_file.name, 'w') as file:
        file.write(cpp_content)
    
    return temp_cpp_file.name


def main():
  args = getArguments()
  print("ARGS MAIN")
  print(args)



  if(args["file_name"] and args["file_name"] != ""):
    demo_file_path = os.path.join(args['uploaded_file'], args['demo_name'] + '.py')
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
      # Split the output into individual commands based on newline
      commands = command_outputs.split('\n')
      # Send each command separately
      send_serial_commands(port, commands)

  if arduino:
      arduino.close()

def compile_and_run_cpp(cpp_file_path):
    executable_path = cpp_file_path.rsplit('.', 1)[0]
    # Include -std=c++11 to specify using the C++11 standard
    compile_command = f"g++ -std=c++11 {cpp_file_path} -o {executable_path}"
    try:
        subprocess.check_call(compile_command, shell=True)
        print("Compilation successful.")
        # Execute the compiled code and capture the output
        output = subprocess.check_output(executable_path, text=True)
        return output.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation or execution: {e}")
    finally:
        # Cleanup
        os.remove(cpp_file_path)
        # Ensure executable_path exists before attempting to remove it
        if os.path.exists(executable_path):
            os.remove(executable_path)
    return ""


def send_serial_commands(port, commands):
    global arduino
    try:
        if arduino is None:
            arduino = serial.Serial(port, 250000)
            time.sleep(2)

        for command in commands:
            start_time=time.time()

            print(f"Sending command to Arduino: {command}")
            arduino.write((command + '\n').encode())
            
            wait_for_acknowledgement()  # Wait for ACK instead of using sleep
            end_time=time.time()
            elapsed_time = end_time - start_time  # Calculate the elapsed time
            print("Elapsed time:", elapsed_time, "seconds")
            
        arduino.write(b"clearCube\n")
     
    except serial.SerialException as e:
        print(f"Error in serial communication: {e}")


if __name__ == '__main__':
    main()
