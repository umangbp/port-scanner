import sys
import argparse
import socket
import threading
import queue
import time
import os
import datetime
import math

from tabulate import tabulate
from operator import itemgetter

start = time.time()

# list to hold result
result = []

# queue object which will be used to store tasks which are waiting for execution
q = queue.Queue()

# list to hold the threads
threads = []

# total threads that needs to be created
num_worker_threads = 10

# function to scan the specified port on target
# item : port number to scan
# arguments: command line arguments passed by user
def scan_port(item, arguments):
    
	try:

		# creating socket object
		net_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		net_socket.settimeout(1)

		# try to connect to target on specified port
		net_socket.connect((arguments.target, item))
		net_socket.close()

		try:
			service = socket.getservbyport(item, 'tcp')
		except Exception as e:
			service = "Unknown"

		# append the result to the final result list
		result.append([item, 'OPEN', service])
  
	except:
     
		return False

# a thread function which will be called whenever the will be created
# this function takes a port number from the queue and scan that port using scan_port function
# arguments : commandline arguments passed by user
def worker(arguments):

    try:

        while True:
            item = q.get()
            if item is None:
                break
            scan_port(item, arguments)
            q.task_done()

    except KeyboardInterrupt:
        terminate_program()

# function to generate output based on users parameter  
# arguments : commandline arguments passed by user
def generate_output(arguments):
    
    # if user selects to get output in file 
	if arguments.output:

		# open the file specified by user
		# this will also create a file if file does not already exist
		output_file = open(arguments.output, 'w+')

		# writing output to the file
		output_file.write("Starting port scan at - {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
		output_file.write("\nGenerating scan report for {} \n\n".format(arguments.target))
		output_file.write(tabulate(result, headers=['PORT', 'STATUS', 'SERVICE'], tablefmt='plain'))
		output_file.write("\n\nScan done: 1 IP address scanned in {} seconds".format(time.time() - start))
		output_file.close()

		# printing the message on console 
		print("Scan done: 1 IP address scanned in {} seconds".format(time.time() - start))
		print("Open file {} to see the output".format(arguments.output))

	# print output on console
	else:

		print(tabulate(result, headers=['PORT', 'STATE', 'SERVICE'], tablefmt='plain'))
		print("\nScan done: 1 IP address scanned in {} seconds".format(time.time()-start))
    

# function to stop all worker threads and terminate the program
def terminate_program():
    
    # stop workers
	for i in range(num_worker_threads):
		q.put(None)

	# waiting till all threads finishes execution
	for t in threads:
		t.join()

	sys.exit()

# Main method
def main():

	start_port = 1
	end_port = 65535

	# creating object of argument parser
	parser = argparse.ArgumentParser()

	# add optional and required arguments that user can enter
	parser.add_argument("target", help='HOST ADDRESS TO SCAN')
	parser.add_argument("-p", "--ports", help="<port range>: Only scan specified ports", action="store")
	parser.add_argument("-f", "--full", help="Fast scan - only scan first 1000 TCP ports", action="store_true")
	parser.add_argument("-o", "--output", help="<output file>: Output file name", action="store")

	arguments = parser.parse_args()
 
	
	# creating multiple worker threads to make port scan faster
	for i in range(num_worker_threads):

		t = threading.Thread(target=worker, args=(arguments,))
		t.start()
		threads.append(t)	
 
 
	# check if user has passed -p or --ports arguments i.e
	if arguments.ports:

		# check if user has provided range of ports or single port i.e -p10 or -p10-20
		if '-' in arguments.ports:

			port_arg = arguments.ports

			# splitting string from - if user has given the range of ports
			port_range = port_arg.split('-')

			# getting start port and end port to scan
			start_port = int(port_range[0])
			end_port = int(port_range[1])

		# if user only provides single port in argument i.e -p10
		else:
    
			if(arguments.ports.isdigit()):
				start_port = int(arguments.ports)
				end_port = start_port
			else:
				print("\n\033[1;31m Invalid value for argument -p or --port\033[0m \n")
				
				# call function to terminate program
				terminate_program()
    			

	# if user passes -f or --fast argument then only scan first 1000 ports
	elif arguments.full:
		start_port = 1
		end_port = 65535
  
	# if user does not specify ports arguments then scan all 65535 ports by default
	else:

		start_port = 1
		end_port = 1000

 
	print("\nStarting port scan at - {}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
	print("Generating scan report for {} \n".format(arguments.target))
 
	# iterating over range of ports and put them into queue for execution 
	for portNumber in range(start_port, end_port + 1):
		q.put(portNumber)
 
	# block until all tasks are done
	q.join()

    # stop workers
	for i in range(num_worker_threads):
		q.put(None)

	# waiting till all threads finishes execution
	for t in threads:
		t.join()
	
	# sorting result
	result.sort(key=itemgetter(0))
	
	# calling function to generate output according to the arguments passed by the user
	# prints output on screen or write to a file specified in the arguments
	generate_output(arguments)

# invoking main function
if __name__ == '__main__':

	main()