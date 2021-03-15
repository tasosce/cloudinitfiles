# sudo apt install python-pip
# pip install psutil
# pip install requests
# pip install python-firebase

import os
import socket
import json
import platform
import time
from collections import OrderedDict
from firebase import firebase
from datetime import datetime

try:
        import requests
except ImportError:
        os.system('pip install requests')
        import requests

try:
        import psutil
except ImportError:
        os.system('pip install psutil')
        import psutil


#------------------------------------------------------------
#--------------------- CREATE FOLDERS  ----------------------
#------------------------------------------------------------


if os.path.exists('/home/tasos/export'):
        pass
else:
        os.system('mkdir /home/tasos/export')
        os.system('touch /home/tasos/export/specs.json')


#------------------------------------------------------------
#------------------ VM's RAM, DISK, CPUs --------------------
#------------------------------------------------------------


cpu = psutil.cpu_count()

mem = psutil.virtual_memory()
ram_total = mem.total / (1024 ** 3)
ram_used = mem.used / (1024 ** 3)
ram_free = mem.free / (1024 ** 3)

disk = psutil.disk_usage('/')
disk_total = disk.total / (1024 ** 3)
disk_used = disk.used / (1024 ** 3)
disk_free = disk.free / (1024 ** 3)

net = psutil.net_if_addrs()

hostname = socket.gethostname()

speclist = []
vmspec = OrderedDict()

vmspec['OS Name'] = platform.platform()
vmspec['Hostname'] = hostname
vmspec['VCPUs'] = cpu
ramlst = []
ramspec = OrderedDict()
ramspec['total'] = round(ram_total,2)
ramspec['used'] = round(ram_used,2)
ramspec['free'] = round(ram_free,2)
ramlst.append(ramspec)
vmspec['RAM'] = ramlst
disklst = []
diskspec = OrderedDict()
diskspec['total'] = round(disk_total,2)
diskspec['used'] = round(disk_used,2)
diskspec['free'] = round(disk_free,2)
disklst.append(diskspec)
vmspec['Disk'] = disklst
niclst = []
for i in net:
        nicspec = OrderedDict()
        nicspec['name'] = i
        nicspeclst = []
        for j in range(len(net[i])):
                nicspecfam = OrderedDict()
                if str(net[i][j].family) == "AddressFamily.AF_INET":
                        nicspecfam['ip version'] = 'IPv4'
                elif str(net[i][j].family) == 'AddressFamily.AF_INET6':
                        nicspecfam['ip version'] = 'IPv6'
                elif str(net[i][j].family) == 'AddressFamily.AF_PACKET':
                        nicspecfam['ip version'] = 'Hardware'
                nicspecfam['address'] = str(net[i][j].address)
                nicspecfam['netmask'] = str(net[i][j].netmask)
                nicspecfam['broadcast'] = str(net[i][j].broadcast)
                #management net ip
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
                nicspeclst.append(nicspecfam)
        nicspec['specs'] = nicspeclst
        niclst.append(nicspec)

vmspec['NIC'] = niclst
vmspec['management_net ip'] = ip
addresses = ['8.8.8.8']
response = os.system('ping -c 1 ' + addresses[0])
if response == 0:
        vmspec['status'] = 'connected'
else:
        vmspec['status'] = 'disconnected'

speclist.append(vmspec)

with open('/home/tasos/export/specs.json','w') as f1:
        json.dump(speclist,f1, indent=4, separators=(',',':'), sort_keys=False)
        #add trailing newline for POSIX compatibility
        f1.write('\n')

firebase = firebase.FirebaseApplication("https://validator-243a5.firebaseio.com/",None)

table = {
        'status': 'activated'
}

result1 = firebase.put('/InstanceTable','object',table)
timestamp = datetime.now()

data = {
        'DNS name': vmspec['Hostname'],
        'Disk(gb)': diskspec['total'],
        'IP address': vmspec['management_net ip'],
        'OS': vmspec['OS Name'],
        'Ram(gb)': ramspec['total'],
        'Status': vmspec['status'],
        'vCPU': vmspec['VCPUs'],
        'timestamp' : timestamp
}

result2 = firebase.put('/VDU/',vmspec['Hostname'],data)
print(result2)


#RAM
ram = psutil.virtual_memory()
ram_used = ram.used / (1024 ** 3)
ram_used = round(ram_used,2)

ramTimestamp = datetime.now()

ramData = {
	'timestamp': ramTimestamp,
	'ram': ram_used,
}


#CPU
cpu_used = psutil.cpu_percent()
cpu_used = round(cpu_used,1)

cpuTimestamp = datetime.now()

cpuData = {
	'timestamp': cpuTimestamp,
	'cpu': cpu_used,
}

result1 = firebase.post('/VDU Timestamps/' + vmspec['Hostname'] + '/ram-timestamps',ramData)

result2 = firebase.post('/VDU Timestamps/' + vmspec['Hostname'] + '/cpu-timestamps',cpuData)

result3 = firebase.get('/Timestamps',None)

result4 = firebase.put('/VDU Timestamps/' + vmspec['Hostname'] + '/','name',vmspec['Hostname'])

while result3['action'] != 'stop':
	result3 = firebase.get('/Timestamps',None)

	#RAM
	ram = psutil.virtual_memory()
	ram_used = ram.used / (1024 ** 3)
	ram_used = round(ram_used,2)

	ramTimestamp = datetime.now()

	print('sending timestamp... ',ramTimestamp,' ',ram_used,'GB')

	ramData = {
		'timestamp': ramTimestamp,
		'ram': ram_used,
	}

	#CPU
	cpu_used = psutil.cpu_percent()
	cpu_used = round(cpu_used,1)

	cpuTimestamp = datetime.now()

	print('sending timestamp... ',cpuTimestamp,' ',cpu_used,'%')

	cpuData = {
		'timestamp': cpuTimestamp,
		'cpu': cpu_used,
	}

	#result1 = firebase.post('/VDU/validator-ns-1-vdu-ubuntu16-1/ram-timestamps',data)
	result1 = firebase.post('/VDU Timestamps/' + vmspec['Hostname'] + '/ram-timestamps',ramData)
	result2 = firebase.post('/VDU Timestamps/' + vmspec['Hostname'] + '/cpu-timestamps',cpuData)
	time.sleep(30)

print('stop sending')
