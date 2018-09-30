import os
import socket
import json
from collections import OrderedDict

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


if os.path.exists('/home/vmuser/export'):
        pass
else:
        os.system('mkdir /home/vmuser/export')
        os.system('touch /home/vmuser/export/specs.json')


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


#------------------------------------------------------------
#-------------------- CREATE JSON FILE ----------------------
#------------------------------------------------------------


speclist = []
vmspec = OrderedDict()

vmspec['OS Name'] = os.name
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
                #management net ip
                if '10.0.10.' in nicspecfam['address']:
                        ip = nicspecfam['address']
                nicspecfam['netmask'] = str(net[i][j].netmask)
                nicspecfam['broadcast'] = str(net[i][j].broadcast)
                nicspeclst.append(nicspecfam)
        nicspec['specs'] = nicspeclst
        niclst.append(nicspec)

vmspec['NIC'] = niclst
vmspec['management_net ip'] = ip

speclist.append(vmspec)

with open('/home/vmuser/export/specs.json','w') as f1:
        json.dump(speclist,f1, indent=4, separators=(',',':'), sort_keys=False)
        #add trailing newline for POSIX compatibility
        f1.write('\n')


url = 'http://10.0.100.151:6868/api'
response = requests.post(url, json = speclist)
print(response)
