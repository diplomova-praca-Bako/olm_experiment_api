#!/usr/bin/python3

import argparse
import subprocess
import os
import re
import time
import tempfile


def main():
    args = getArguments()
    
    code_to_run=''

    if args.get("demo_name"):
        demo_file_path = os.path.join(args['uploaded_file'], args['demo_name'] + '.cpp')
        try:
            with open(demo_file_path, 'r') as file:
                demo_content = file.read()
            code_to_run=demo_content

        except FileNotFoundError:
            print(f"File '{demo_file_path}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    elif args.get("uploaded_code_file"):
        code_to_run=args["uploaded_code_file"]


    else:
        code_to_run=args.get("cpp_code", "")
    

    cpp_file_path = create_cpp_file_from_template(code_to_run)
    arduino_instructions = generate_arduino_instructions(cpp_file_path)

    full_arduino_code = generate_arduino_code(arduino_instructions)
    
    compile_and_upload(full_arduino_code, args["port"])

    time.sleep(30)
    clear_cube(args["port"])

def getArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port")
    parser.add_argument("--input")
    parser.add_argument("--output")
    args = parser.parse_args()

    input_str = args.input

    keys = ['cpp_code', 'uploaded_code_file', 'uploaded_file', 'demo_name']
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

def clear_cube(port):
  empty_sketch =  '''
void setup(){}

void loop(){}
'''
  compile_and_upload(empty_sketch, port)

def create_cpp_file_from_template(cpp_code):
    cpp_template = '''
#include <iostream>
#include <vector>

namespace SafeAPI {{

  void setLed(int x, int y, int z) {{
      std::cout << "setLed(" << x << "," << y << "," << z << ");" << std::endl;
  }}

  void clearLed(int x, int y, int z) {{
      std::cout << "clearLed(" << x << "," << y << "," << z << ");" << std::endl;
  }}

  void clearCube() {{
      std::cout << "clearCube();" << std::endl;
  }}

  void sleep(int millis) {{
      std::cout << "sleep(" << millis << ");" << std::endl;
  }}
}}

int main() {{
    using namespace SafeAPI;

    {cpp_code}
    return 0;
}}
'''
    # Ensure variable name in format matches the placeholder
    cpp_content = cpp_template.format(cpp_code=cpp_code)

    # Save to a temporary file
    temp_cpp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".cpp")
    with open(temp_cpp_file.name, 'w') as file:
        file.write(cpp_content)
    
    return temp_cpp_file.name

def generate_arduino_instructions(cpp_file_path):
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
            print(f"Process timed out.")
    except subprocess.CalledProcessError as e:
        print(f"Error during compilation or execution: {e}")
    finally:
        # Cleanup
        os.remove(cpp_file_path)
        if os.path.exists(executable_path):
            os.remove(executable_path)

    lines = output.splitlines()[:1000]     # Split the output into lines and get only the first 1000 because otherwise compilation takes too long

    output = "\n".join(lines)
    return output

def generate_arduino_code(cpp_code_snippet):
    arduino_code_template = '''
#include <avr/interrupt.h>
#include <string.h>
#include <Arduino.h>
#define AXIS_X 1
#define AXIS_Y 2
#define AXIS_Z 3

volatile unsigned char cube[8][8];
volatile int current_layer = 0;

void setup(){{
  int i;
  
  for(i=0; i<14; i++)
    pinMode(i, OUTPUT);
  
  // pinMode(A0, OUTPUT) as specified in the arduino reference didnt work. So I accessed the registers directly.
  DDRC = 0xff;
  PORTC = 0x00;
  
  // Reset any PWM configuration that the arduino may have set up automagically!
  TCCR2A = 0x00;
  TCCR2B = 0x00;

  TCCR2A |= (0x01 << WGM21); // CTC mode. clear counter on TCNT2 == OCR2A
  OCR2A = 10; // Interrupt every 25600th cpu cycle (256*100)
  TCNT2 = 0x00; // start counting at 0
  TCCR2B |= (0x01 << CS22) | (0x01 << CS21); // Start the clock with a 256 prescaler
  
  TIMSK2 |= (0x01 << OCIE2A);
}}

ISR (TIMER2_COMPA_vect)
{{
  int i;
  
  // all layer selects off
  PORTC = 0x00;
  PORTB &= 0x0f;
  
  PORTB |= 0x08; // output enable off.
  
  for (i=0; i<8; i++)
  {{
    PORTD = cube[current_layer][i];
    PORTB = (PORTB & 0xF8) | (0x07 & (i+1));
  }}
  
  PORTB &= 0b00110111; // Output enable on.
  
  if (current_layer < 6)
  {{
    PORTC = (0x01 << current_layer);
  }} else if (current_layer == 6)
  {{
    digitalWrite(12, HIGH);
  }} else
  {{
    digitalWrite(13, HIGH);
  }}
  
  current_layer++;
  
  if (current_layer == 8)
    current_layer = 0;
}}

void loop()
{{
  {}
}}



// ==========================================================================================
//   Draw functions
// ==========================================================================================


// Set a single voxel to ON
void setLed(int x, int y, int z)
{{
  if (inrange(x,y,z))
    cube[z][y] |= (1 << x);
}}


// Set a single voxel to OFF
void clearLed(int x, int y, int z)
{{
  if (inrange(x,y,z))
    cube[z][y] &= ~(1 << x);
}}

// This function validates that we are drawing inside the cube.
unsigned char inrange(int x, int y, int z)
{{
  if (x >= 0 && x < 8 && y >= 0 && y < 8 && z >= 0 && z < 8)
  {{
    return 0x01;
  }} else
  {{
    // One of the coordinates was outside the cube.
    return 0x00;
  }}
}}

// Get the current status of a voxel
unsigned char getLed(int x, int y, int z)
{{
  if (inrange(x,y,z))
  {{
    if (cube[z][y] & (1 << x))
    {{
      return 0x01;
    }} else
    {{
      return 0x00;
    }}
  }} else
  {{
    return 0x00;
  }}
}}

void clearCube(){{
    int z;
    int y;
    for (z = 0; z < 8; z++) {{
        for (y = 0; y < 8; y++) {{
            cube[z][y] = 0x00;
        }}
    }}
}}

void sleep(int millis){{
  delay(millis);
}}
'''

    
    # Insert the C++ code snippet into the template
    return arduino_code_template.format(cpp_code_snippet)

def compile_and_upload(code, port, board_type="arduino:avr:uno"):
    # Create a temporary directory to hold the sketch
    temp_dir = "temp_sketch"
    os.makedirs(temp_dir, exist_ok=True)

    # Write the Arduino code to a .ino file in the temporary directory
    sketch_path = os.path.join(temp_dir, "temp_sketch.ino")
    with open(sketch_path, "w") as file:
        file.write(code)

    # Compile and upload using Arduino CLI
    compile_cmd = f"arduino-cli compile --fqbn {board_type} {temp_dir}"
    upload_cmd = f"arduino-cli upload -p {port} --fqbn {board_type} {temp_dir}"

    try:
        subprocess.run(compile_cmd, check=True, shell=True)
        subprocess.run(upload_cmd, check=True, shell=True)
        print("Upload successful")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")

    # Clean up: remove the temporary directory
    subprocess.run(f"rm -rf {temp_dir}", shell=True)

if __name__ == '__main__':
    main()