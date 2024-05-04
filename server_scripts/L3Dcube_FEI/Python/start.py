#!/usr/bin/python3

import argparse
import os
import subprocess
import time
import math
import random
import re
from io import StringIO
import sys

def wait_for_acknowledgement():
    global arduino
    while True:
        if arduino.in_waiting > 0:
            line = arduino.readline().decode().strip()
            if line == "ACK":
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

    # time.sleep(30)
    # clear_cube(args["port"])

def clear_cube(port):
  empty_sketch =  '''
void setup(){}

void loop(){}
'''
  compile_and_upload(empty_sketch, port)


def run_process(code, port):
    dynamic_code=create_text_from_dynamic_code(code)
    print(dynamic_code)
    full_arduino_code=generate_arduino_code(dynamic_code)
    print(full_arduino_code)
    compile_and_upload(full_arduino_code,port)




def setvoxel(x, y, z):
    print(f"setvoxel({x}, {y}, {z});")

def clrvoxel(x, y, z):
    print(f"clrvoxel({x}, {y}, {z});")

def delay(millis):
    print(f"delay({millis});")


def create_text_from_dynamic_code(dynamic_code): # obmedzit cas behu na par sekund
    local_scope = {
        'setvoxel': setvoxel,
        'clrvoxel': clrvoxel,
        'delay': delay,
        'math': math,
        'random': random
    }

    # Redirect standard output to a StringIO object
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    # Execute the dynamic code
    try:
        exec(dynamic_code, local_scope)
    except Exception as e:
      print(f"Error executing dynamic code: {e}")
      raise(e)



    # Retrieve the output from the StringIO object
    dynamic_text = sys.stdout.getvalue()

    # Restore the original standard output
    sys.stdout = old_stdout

    # Return the captured output
    return dynamic_text


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







def generate_arduino_code(c_code_snippet):
    arduino_code_template = '''
#include <avr/interrupt.h>
#include <string.h>
#define AXIS_X 1
#define AXIS_Y 2
#define AXIS_Z 3

volatile unsigned char cube[8][8];
volatile int current_layer = 0;

const int cube_size = 8;

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
void setvoxel(int x, int y, int z)
{{
  if (inrange(x,y,z))
    cube[z][y] |= (1 << x);
}}


// Set a single voxel to OFF
void clrvoxel(int x, int y, int z)
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
unsigned char getvoxel(int x, int y, int z)
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


// Fill a value into all 64 byts of the cube buffer
// Mostly used for clearing. fill(0x00)
// or setting all on. fill(0xff)
void fill (unsigned char pattern)
{{
  int z;
  int y;
  for (z=0;z<8;z++)
  {{
    for (y=0;y<8;y++)
    {{
      cube[z][y] = pattern;
    }}
  }}
}}
'''
    return arduino_code_template.format(c_code_snippet)




if __name__ == '__main__':
    main()
