import os
import sys
import json
import subprocess
import time
from collections import OrderedDict
try:
	import yaml
except ImportError:
	os.system('pip install pyyaml')
	import yaml

try:
        from flask import Flask, request, make_response
except ImportError:
        os.system('pip install Flask')
        from flask import Flask, request, make_response

#------------------------------------------------------------
#---- Create aggent dir , instances.json and vmscan.txt -----
#------------------------------------------------------------

if os.path.exists('/opt/stack/agent'):
        os.system('sudo route add -net 10.0.10.0/24 gw 10.0.100.233 >/dev/null 2>&1')
        os.system('openstack server list -f json > /opt/stack/agent/instances.json')
        os.system('openstack flavor list -f json > /opt/stack/agent/flavors.json')
else:
        os.system('sudo route add -net 10.0.10.0/24 gw 10.0.100.233 >/dev/null 2>&1')
        os.system('mkdir /opt/stack/agent')
        os.system('touch /opt/stack/agent/vmscan.txt')
        os.system('touch /opt/stack/agent/instances.json')
        os.system('touch /opt/stack/agent/flavors.json')
        os.system('mkdir /opt/stack/agent/ns')
        os.system('mkdir /opt/stack/agent/vnf')
        os.system('mkdir /opt/stack/agent/export')
        os.system('touch /opt/stack/agent/export/osm_topology.json')
        os.system('mkdir /opt/stack/agent/vms_json_files')
        os.system('openstack server list -f json > /opt/stack/agent/instances.json')
        os.system('openstack flavor list -f json > /opt/stack/agent/flavors.json')
        print('\n- Directory \'agent\' has been created \n')

if  os.stat('/opt/stack/agent/instances.json').st_size == 0:
	print('\n!! The instances.json file is empty')
	print('!! Please check if the credentials of openstack are right')
	print('!! Possible error with the open.rc file')
	print('!! Try to source the open.rc file\n')
	sys.exit()
else:
	with open('/opt/stack/agent/instances.json') as f1:
		data = json.load(f1)

	with open('/opt/stack/agent/flavors.json') as f7:
		flavor = json.load(f7)


#------------------------------------------------------------
#---------- Download and Install OSM Client -----------------
#------------------------------------------------------------

if os.path.exists('/usr/lib/python2.7/dist-packages/osmclient'):
	print('\n- OSM Client is already installed \n')
	os.system('sudo route add -net 10.135.97.0/24 gw 10.0.100.160 >/dev/null 2>&1')
	os.system('sudo route add -net 10.180.205.0/24 gw 10.0.100.160 >/dev/null 2>&1')
	os.environ['OSM_HOSTNAME'] = '10.180.205.228'
else:
	os.system('curl http://osm-download.etsi.org/repository/osm/debian/ReleaseTHREE/OSM%20ETSI%20Release%20Key.gpg | sudo apt-key add -')
	os.system('sudo add-apt-repository -y "deb [arch=amd64] http://osm-download.etsi.org/repository/osm/debian/ReleaseTHREE stable osmclient"')
	os.system('sudo apt-get update')
	os.system('sudo apt-get install -y python-osmclient')
	os.system('sudo pip install python-magic')
	os.system('sudo route add -net 10.135.97.0/24 gw 10.0.100.160 >/dev/null 2>&1')
	os.system('sudo route add -net 10.180.205.0/24 gw 10.0.100.160 >/dev/null 2>&1')
	os.environ['OSM_HOSTNAME'] = '10.180.205.228'


#------------------------------------------------------------
#---------------------- TOPOLOGY ----------------------------
#------------------------------------------------------------


print('\n|------------ Network Topology ------------|\n')


vms = len(data)
ns = []
vnf = []

for i in range(vms):
        if '.' in data[i]['Name']:
                if (data[i]['Name'].split('.')[0]) not in ns:
                        ns.append((data[i]['Name'].split('.')[0]))
                if (data[i]['Name'].split('.')[1]) not in vnf:
                        vnf.append((data[i]['Name'].split('.')[1]))

print ('Instances  : %d'%(vms))
print ('NS         : ' + str(', '.join(ns)))
print ('VNF        : ' + str(', '.join(vnf)))


#------------------------------------------------------------
#---------- PREVIOUS AND NEW INSTANCES/NS/VNF ---------------
#------------------------------------------------------------

pre_vms_names = []
new_vms_names = []
cur_vms_names = []

#(Read previous instances)

if os.stat('/opt/stack/agent/vmscan.txt').st_size == 0:
        print('\n\n+-----------------------------------+')
        print('| !! The file vmscan.txt is empty   |')
        print('| !! There are no deleted instances |')
        print('+-----------------------------------+')
else:
        with open('/opt/stack/agent/vmscan.txt','r') as f2:
                 pre_vms_names = json.load(f2)

#(Read new instances)

for i in range(vms):
        if data[i]['Name'] not in pre_vms_names:
                new_vms_names.append(data[i]['Name'])

#(Read current instances)

for i in range(vms):
        cur_vms_names.append(data[i]['Name'])


#------------------------------------------------------------

#(Print deleted instances)

print('\n\n|----------- Deleted Instances ------------|\n')

if not pre_vms_names or pre_vms_names == cur_vms_names:
        print (' No instances has been deleted')
else:
        for i in range(len(pre_vms_names)):
                if pre_vms_names[i] not in cur_vms_names:
                        print (pre_vms_names[i])
print()

#(Print new instances)

print('\n|------------- New Instances --------------|\n')

if not new_vms_names:
        print(' There are no new instances')
else:
        for i in range(len(new_vms_names)):
                print(new_vms_names[i])
print()

#(Print current instances)

print('\n|----------- Current Instances ------------|\n')

if not cur_vms_names:
        print(' There are no instances')
else:
        for i in range(len(cur_vms_names)):
                print(cur_vms_names[i])

print('\n')

#(Load current instances to vmscan.txt)

with open('/opt/stack/agent/vmscan.txt','w') as f3:
        json.dump(cur_vms_names,f3)


#------------------------------------------------------------
#-------------- LOAD THE XAML FILES OF OSM ------------------
#------------------------------------------------------------

#(Create ns and vnf yaml files)

vnf_file = []

if not ns:
        print('\n No NS found \n')
else:
        for n in ns:
                os.system('osm ns-show ' + n + ' --literal > /opt/stack/agent/ns/' + n + '.yaml')
                if not vnf:
                        print('\n No VNF found \n')
                else:
                        with open('/opt/stack/agent/ns/' + n + '.yaml','r') as f4:
                                nsd = yaml.safe_load(f4)
                        for v in vnf:
                                for i in range(len(nsd['nsd']['constituent-vnfd'])):
                                        vnf_name = 'default__' + n + '__' + v + '__' + str(nsd['nsd']['constituent-vnfd'][i]['member-vnf-index'])
                                        if os.path.exists('/opt/stack/agent/vnf/' + vnf_name + '.yaml'):
                                                #file exist
                                                vnf_file.append(vnf_name)
                                        else:
                                                os.system('osm vnf-show ' + vnf_name + ' --literal >> /opt/stack/agent/vnf/' + vnf_name + '.yaml')
                                                not_found = ['vnf ' + vnf_name + ' not found\n']
                                                #delete the empty yaml files
                                                with open('/opt/stack/agent/vnf/' + vnf_name + '.yaml','r') as f5:
                                                        vnf_data = f5.readlines()
                                                if vnf_data == not_found:
                                                        os.system('rm -r /opt/stack/agent/vnf/' + vnf_name + '.yaml')


#------------------------------------------------------------
#-------------------- PING THE INSTANCES --------------------
#------------------------------------------------------------


instances_ip_lst =[]

for i in range(vms):
	if 'management_net' in data[i]['Networks']:
		ins_name = (data[i]['Name'])
		ins_ip = ((data[i]['Networks'].split('=')[1]).split(';')[0])
		instances_ip_info = {}
		instances_ip_info['Name'] = ins_name
		instances_ip_info['IP'] = ins_ip
		instances_ip_info['State'] = 'NONE'
		instances_ip_lst.append(instances_ip_info)


print ('+------------------------------+------------+')
print ('|            Ping              |  Response  |')
print ('+------------------------------+------------+')
print ('+------------------------------+------------+')

for i in range(len(instances_ip_lst)):
	response = os.system("ping -c 1 " + instances_ip_lst[i]['IP'] + " >/dev/null 2>&1")
	spaces = (30 - len(instances_ip_lst[i]['Name']) - 1) * ' ' 
	if response == 0:
		instances_ip_lst[i]['State'] = 'ACTIVE'
		print ('| %s%s| is up   !  |'%(instances_ip_lst[i]['Name'],spaces))
		print ('+------------------------------+------------+')
	else:
		instances_ip_lst[i]['State'] = 'SHUTOFF'
		print ('| %s%s| is down !  |'%(instances_ip_lst[i]['Name'],spaces))
		print ('+------------------------------+------------+')


print ()


#------------------------------------------------------------
#----- CREATE THE FINAL JSON DESCRIPTOR OF THE TOPOLOGY -----
#------------------------------------------------------------


#(Flavors)
flv = len(flavor)

#(OSM instances names)
osm_instances_names = []

for i in range(len(instances_ip_lst)):
	osm_instances_names.append(instances_ip_lst[i]['Name'])

net_topology_info = []

for i in cur_vms_names:
	if i not in osm_instances_names:
		for j in range(vms):
                        if data[j]['Name'] == i:
                                specs = OrderedDict()
                                instance_info = OrderedDict()
                                instance_info['Name'] =  data[j]['Name']
                                instance_info['Status'] = data[j]['Status']
                                instance_info['Networks'] = data[j]['Networks']
                                instance_info['OpenStack ID'] = data[j]['ID']
                                instance_info['Image'] = data[j]['Image']
                                for k in range(flv):
                                        if data[j]['Flavor'] == flavor[k]['Name']:
                                                specs['Name'] = flavor[k]['Name']
                                                specs['RAM'] = flavor[k]['RAM']
                                                specs['VCPUs'] = flavor[k]['VCPUs']
                                                specs['Disk'] = flavor[k]['Disk']
                                instance_info['Flavor'] = specs
                                net_topology_info.append(instance_info)
	else:
		for j in range(vms):
                        if data[j]['Name'] == i:
                                specs = OrderedDict()
                                instance_info = OrderedDict()
                                instance_info['Name'] =  data[j]['Name']
                                instance_info['Status'] = data[j]['Status']
                                instance_info['OpenStack ID'] = data[j]['ID']
                                instance_info['Image'] = data[j]['Image']
                                for k in range(flv):
                                        if data[j]['Flavor'] == flavor[k]['Name']:
                                                specs['Name'] = flavor[k]['Name']
                                                specs['RAM'] = flavor[k]['RAM']
                                                specs['VCPUs'] = flavor[k]['VCPUs']
                                                specs['Disk'] = flavor[k]['Disk']
                                instance_info['Flavor'] = specs
                                vnf_name = (instance_info['Name'].split('.')[1])
                                vm_name = (instance_info['Name'].split('.')[3])
                                netlst = []
                                for v in vnf_file:
                                        if vnf_name in v:
                                                with open('/opt/stack/agent/vnf/' + v + '.yaml','r') as f8:
                                                        vmd = yaml.safe_load(f8)
                                                for ci in range(len(vmd['vnfd']['vdu'])):
                                                        if vm_name == vmd['vnfd']['vdu'][ci]['name']:
                                                                instance_info['Cloud-init-file'] = vmd['vnfd']['vdu'][ci]['cloud-init-file']
                                                nets = {}
                                                nets['Networks'] = data[j]['Networks']
                                                netlst.append(nets)
                                                for cp in range(len(vmd['connection-point'])):
                                                        net = OrderedDict()
                                                        if vmd['connection-point'][cp]['ip-address'] in data[j]['Networks']:
                                                                net['ip-address'] = vmd['connection-point'][cp]['ip-address']
                                                                net['mac-address'] = vmd['connection-point'][cp]['mac-address']
                                                                cp_info = OrderedDict()
                                                                cp_info['name'] = vmd['connection-point'][cp]['name']
                                                                for t in range(len(vmd['vnfd']['connection-point'])):
                                                                        if vmd['vnfd']['connection-point'][t]['name'] == cp_info['name']:
                                                                                cp_info['type'] = vmd['vnfd']['connection-point'][t]['type']
                                                                        else:
                                                                                pass
                                                                for c in range(len(vmd['vnfd']['vdu'])):
                                                                        for p in range(len(vmd['vnfd']['vdu'][c]['interface'])):
                                                                                for key in vmd['vnfd']['vdu'][c]['interface'][p]:
                                                                                        if key == 'external-connection-point-ref':
                                                                                                if vmd['vnfd']['vdu'][c]['interface'][p]['external-connection-point-ref'] == cp_info['name']:
                                                                                                        cp_info['interface type'] = vmd['vnfd']['vdu'][c]['interface'][p]['type']
                                                                                        elif key == 'internal-connection-point-ref':
                                                                                                if vmd['vnfd']['vdu'][c]['interface'][p]['internal-connection-point-ref'] == cp_info['name']:
                                                                                                        cp_info['interface type'] = vmd['vnfd']['vdu'][c]['interface'][p]['type']
                                                                cplst = []
                                                                cplst.append(cp_info)
                                                                net['connection-points'] = cplst
                                                                netlst.append(net)
                                                instance_info['VNF ID'] = vmd['vnfd']['id']
                                instance_info['Networks'] =  netlst
                                net_topology_info.append(instance_info)


with open('/opt/stack/agent/export/osm_topology.json','w') as f6:
	json.dump(net_topology_info, f6, indent=4, separators=(',',':'), sort_keys=False)
	#add trailing newline for POSIX compatibility
	f6.write('\n')

app = Flask(__name__)

@app.route('/api',methods=['GET','POST'])
def api():
	if request.method == 'POST':
		templst = []
		tempdict = OrderedDict()
		vmdata = request.get_json()
		tempdict['OS Name'] = request.json[0]['OS Name']
		tempdict['Hostname'] = request.json[0]['Hostname']
		tempdict['VCPUs'] = request.json[0]['VCPUs']
		tempdict['RAM'] = request.json[0]['RAM']
		tempdict['Disk'] = request.json[0]['Disk']
		tempdict['NIC'] = request.json[0]['NIC']
		tempdict['management_net ip'] = request.json[0]['management_net ip']
		templst.append(tempdict)
		mip = request.json[0]['management_net ip']
		if os.path.exists('/opt/stack/agent/vms_json_files/vm_' + str(mip) + '.json'):
			with open('/opt/stack/agent/vms_json_files/vm_' + str(mip) + '.json','w') as f8:
				json.dump(templst, f8, indent=4, separators=(',',':'), sort_keys=False)
				#add trailing newline for POSIX compatibility
				f8.write('\n')
		else:
			os.system('touch /opt/stack/agent/vms_json_files/vm_' + str(mip) + '.json')
			with open('/opt/stack/agent/vms_json_files/vm_' + str(mip) + '.json','w') as f8:
				json.dump(templst, f8, indent=4, separators=(',',':'), sort_keys=False)
				#add trailing newline for POSIX compatibility
				f8.write('\n')
	return make_response("",200)

if __name__ == "__main__":
	app.run(host = "10.0.100.151", port = 6868)
