import csv
from datetime import datetime
import re
import sys

# PET helper by Norah Vii

# Open the CSV file
with open('petref.csv', 'r') as f:
    # Use the csv.reader() function to read the file
    reader = csv.reader(f)
    # Convert the CSV data into a list of rows
    data = list(reader)

# Skip (0: tracer_name)
data = data[1:]
# Display the options to the user
for i, row in enumerate(data):
    print(f'{i+1}: {row[1]}')

# Gather input
try:
    # Ask for tracer
    selection = int(input('Select a tracer: '))
    # Select tracer
    selected_tracer = data[selection-1][1]
    # Print selected tracer
    print(f'You selected: {selected_tracer}')
    # Ask for start time
    input_start_time = str(input("""(0054,0016)	Radiopharmaceutical Start Time:
Enter Injection Time: """))
    # Ask for series time
    input_end_time = str(input("""(0008,0031)	Series Time:
Enter Scan Start Time: """))

except KeyboardInterrupt:
    # End if input interrupted
    print("\nProgram Terminated")
    sys.exit()

# Parse time input with regex
start_list = re.findall('\d{1,2}', input_start_time)
end_list = re.findall('\d{1,2}', input_end_time)
# Reformat times
start_time = ''.join(start_list)
end_time = ''.join(end_list)
# Convert time string to datetime
t1 = datetime.strptime(start_time, "%H%M%S")
print('Start time:', t1.time())
t2 = datetime.strptime(end_time, "%H%M%S")
print('End time:', t2.time())
# Get difference
difference = t2 - t1
delta = round(difference.total_seconds() / 60.0)
# Time difference in seconds
print(f"Delay is {delta} mins")

# Populate variables based on selected tracer
# index = data[selection-1][0]
# tracer_name = data[selection-1][1]
desired_static_delay = data[selection-1][2]
desired_dynamic_delay = data[selection-1][3]
mst = data[selection-1][4]
mdt = data[selection-1][5]
model_state_if_dynamic = data[selection-1][6]
model_state_if_static = data[selection-1][7]
static_minimum = data[selection-1][8]
static_maximum = data[selection-1][9]
dynamic_minimum = data[selection-1][10]
dynamic_maximum = data[selection-1][11]

# Colors
yellow,red,green,cl = '\033[33m','\033[31m','\033[32m','\033[0m'

try:
    # Print values to console:
    print(f"MST: {mst}")
    print(f"MDT: {mdt}")
    print(f"Optimal static delay: {desired_static_delay}")
    print(f"Optimal dynamic delay: {desired_dynamic_delay}")
    # Print green if optimal
    optimal = None
    # Optimal dynamic
    if delta == int(desired_dynamic_delay):
        print(f"{delta} is{green} optimal{cl} for {selected_tracer} (dynamic: {model_state_if_dynamic}).")
        optimal = True
    # Optimal static
    if delta == int(desired_static_delay):
        print(f"{delta} is{green} optimal{cl} for {selected_tracer} (static: {model_state_if_static}).")
        optimal = True
    # Print yellow if sub-optimal
    if not optimal:
        # Sub-optimal dynamic
        if delta in range(int(dynamic_minimum), int(dynamic_maximum)+1):
            print(f"{delta} is{yellow} sub-optimal{cl} for {selected_tracer} (dynamic: {model_state_if_dynamic}).")
            if delta > int(mst):
                print(f"MST exceeded!{red} Adjust MST{cl} ({mst}), always below {dynamic_maximum}:")
            else:
                print("Requires no adjustment:")
            print(f"Dynamic minimum: {dynamic_minimum}")
            print(f"Dynamic maximum: {dynamic_maximum}")
        # Sub-optimal static
        if delta in range(int(static_minimum), int(static_maximum)+1):
            print(f"{delta} is{yellow} sub-optimal{cl} for {selected_tracer} (static: {model_state_if_static}).")
            if delta > int(mst):
                print(f"MST exceeded!{red} Adjust MST{cl} ({mst}), always below {static_maximum}:")
            else:
                print("Requires no adjustment:")
            print(f"Static minimum: {static_minimum}")
            print(f"Static maximum: {static_maximum}")
    # Print red if unacceptable
    if not optimal:
        # Unacceptable dynamic
        if delta > int(dynamic_maximum) and delta < int(static_minimum):
            print(f"{delta} is{red} beyond tolerance{cl} for {selected_tracer} (dynamic: {model_state_if_dynamic}).")
            late_time_dynamic = int(delta) - int(desired_dynamic_delay)
            print(f"Scan started {late_time_dynamic} min(s){red} late{cl}.")
            print(f"Dynamic minimum: {dynamic_minimum}")
            print(f"Dynamic maximum: {dynamic_maximum}")
        # Unacceptable static
        if delta > int(static_maximum):
            print(f"{delta} is{red} beyond tolerance{cl} for {selected_tracer} (static: {model_state_if_static}).")
            late_time_static = int(delta) - int(desired_static_delay)
            print(f"Scan started {late_time_static} min(s){red} late{cl}.")
            print(f"Static minimum: {static_minimum}")
            print(f"Static maximum: {static_maximum}")

except (IndexError,ValueError,KeyError):
    print("Invalid Entry")

print("refroistr: Cerebellum-Cortex")
