import argparse
import docker

parser = argparse.ArgumentParser(description='Socker swarm service discovery')
parser.add_argument('--service_name', type=str, default='', help='service name')
parser.add_argument('--container_id', type=str, default='', help='container ID')
parser.add_argument('--target_port', nargs="+", type=int, default=[], help='service target port')
parser.add_argument('--docker_host', type=str, default='', help='docker host example: tcp://127.0.0.1:2376')
parser.add_argument('--tlscacert', type=str, default='', help="Trust certs signed only by this CA")
parser.add_argument('--tlscert', type=str, default='', help="Path to TLS certificate file")
parser.add_argument('--tlskey', type=str, default='', help="Path to TLS key file")
parser.add_argument("-v", "--verbosity", action="count", default=0, help="increase output verbosity")
args = parser.parse_args()

service_name = args.service_name
container_id = args.container_id
TargetPort = args.target_port

TLSCACERT = args.tlscacert
TLSCERT = args.tlscert
TLSKEY = args.tlskey
DOCKER_HOST = args.docker_host

client = None
if TLSCACERT != '' or TLSCERT != '' or TLSKEY != '' or DOCKER_HOST != '':
    tls_config = docker.tls.TLSConfig(
        client_cert=(TLSCERT, TLSKEY),
        ca_cert=TLSCACERT,
        verify=True,
        assert_hostname=False
    )
    client = docker.DockerClient(base_url=DOCKER_HOST, tls=tls_config)
else:
    client = docker.from_env()

nodes_list = client.nodes.list()
for service in client.services.list(filters={'name': service_name}):
    for task in service.tasks(filters={'desired-state': 'running'}):
        node_id = []
        if container_id != '' and container_id == task['Status']['ContainerStatus']['ContainerID']:
            node_id.append(task['NodeID'])
        elif container_id == '':
            node_id.append(task['NodeID'])

        for node in filter(lambda item: item.attrs['ID'] in node_id, nodes_list):
            node_host = node.attrs['Status']['Addr']

            Ports = []
            if len(TargetPort) > 0:
                Ports = filter(lambda port: int(port['TargetPort']) in TargetPort, service.attrs['Endpoint']['Ports'])
            else:
                Ports = service.attrs['Endpoint']['Ports']

            print("service name: %s" % service.name)
            for Port in Ports:
                print('%(host)s:%(port)s' % {'host': node_host, 'port': Port['PublishedPort']})

