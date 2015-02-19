import os
import time
from fabric.api import local

BRIDGE = {"name": "br0", "addr": "10.0.10.254", "mask": "/24"}
POS1 = {"name": "postgres1", "addr": "10.0.10.1", "image": "nhanaue/postgres"}
POS2 = {"name": "postgres2", "addr": "10.0.10.2", "image": "nhanaue/postgres"}
SHEEP1 = {"name": "sheepdog1", "addr": "10.0.10.11", "image": "nhanaue/sheepdog"}
SHEEP2 = {"name": "sheepdog2", "addr": "10.0.10.12", "image": "nhanaue/sheepdog"}
SHEEP3 = {"name": "sheepdog3", "addr": "10.0.10.13", "image": "nhanaue/sheepdog"}
POS = [POS1, POS2]
SHEEP = [SHEEP1, SHEEP2, SHEEP3]

VDI = {"name": "vdipos", "size": "10G"}
SHARE_SHEEP_DIR = "/var/lib/sheepdog"


def check_user():
    root = False
    outbuf = local("echo $USER", capture=True)
    user = outbuf
    if user == "root":
        root = True

    return root


def install_docker_and_tools():
    print "start install packages of test environment."
    if check_user() is False:
        print "Please running in root."
        return

    local("apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys "
          "36A1D7869245C8950F966E92D8576A8BA88D21E9", capture=True)
    local('sh -c "echo deb https://get.docker.io/ubuntu docker main > /etc/apt/sources.list.d/docker.list"',
          capture=True)
    local("apt-get update", capture=True)
    local("apt-get install -y --force-yes lxc-docker-1.3.2", capture=True)
    local("ln -sf /usr/bin/docker.io /usr/local/bin/docker", capture=True)
    local("gpasswd -a `whoami` docker", capture=True)
    local("apt-get install -y --force-yes iputils-arping", capture=True)
    local("apt-get install -y --force-yes bridge-utils", capture=True)
    local("apt-get install -y --force-yes lv", capture=True)
    local("wget https://raw.github.com/jpetazzo/pipework/master/pipework -O /usr/local/bin/pipework",
          capture=True)
    local("chmod 755 /usr/local/bin/pipework", capture=True)
    # pull docker images
    local("docker pull nhanaue/sheepdog", capture=True)
    local("docker pull nhanaue/postgres", capture=True)


def check_bridge():
    setting_exists = False
    sysfs_name = "/sys/class/net/" + BRIDGE["name"]
    if os.path.exists(sysfs_name):
        setting_exists = True
        return setting_exists
    return setting_exists


def create_bridge():
    cmd = "brctl addbr " + BRIDGE["name"]
    local(cmd, capture=True)
    cmd = "ifconfig " + BRIDGE["name"] + " " + BRIDGE["addr"]
    local(cmd, capture=True)
    cmd = "ifconfig " + BRIDGE["name"] + " up"
    local(cmd, capture=True)


def destroy_bridge():
    sysfs_name = "/sys/class/net/" + BRIDGE["name"]
    if os.path.exists(sysfs_name):
        cmd = "ifconfig " + BRIDGE["name"] + " down"
        local(cmd, capture=True)
        cmd = "brctl delbr " + BRIDGE["name"]
        local(cmd, capture=True)


def set_ipaddr(name, addr):
    addr += "/24"
    cmd = "pipework %s %s %s" % (BRIDGE["name"], name, addr)
    local(cmd, capture=True)


def check_container():
    container_exists = False
    outbuf = local("docker ps -a", capture=True)
    docker_ps = outbuf.split('\n')
    for container in docker_ps:
        container_name = container.split()[-1]
        for pos in POS:
            if pos["name"] == container_name:
                container_exists = True
        for sheep in SHEEP:
            if sheep["name"] == container_name:
                container_exists = True
    return container_exists


def get_container():
    containers = []
    cmd = "docker ps -a | awk '{print $NF}'"
    outbuf = local(cmd, capture=True)
    docker_ps = outbuf.split('\n')
    for container in docker_ps:
        if container != "NAMES":
            containers.append(container.split()[-1])
    return containers


def run_container(instans):
    # image_name = "nhanaue/%s" % instans["name"]
    # cmd = "docker run --privileged=true -v %s:/root/share_volume --name %s -id %s" % (SHARE_DIR, name, image_name)
    if "sheepdog" in instans["name"]:
        cmd = "docker run --privileged=true --name %s -v %s:%s -id %s" \
            % (instans["name"], SHARE_SHEEP_DIR, SHARE_SHEEP_DIR, instans["image"])
    else:
        cmd = "docker run --privileged=true --name %s -id %s" % (instans["name"], instans["image"])

    local(cmd, capture=True)
    set_ipaddr(instans["name"], instans["addr"])


def stop_container(name):
    cmd = "docker rm -f " + name
    local(cmd, capture=True)


def check_share_dir():
    dir_exists = False
    for sheep in SHEEP:
        dir = "%s/%s" % (SHARE_SHEEP_DIR, sheep["name"])
        if os.path.exists(dir):
            dir_exists = True
            return dir_exists
    return dir_exists


def make_share_dir():
    for sheep in SHEEP:
        cmd = "mkdir %s/%s" % (SHARE_SHEEP_DIR, sheep["name"])
        local(cmd, capture=True)


def delete_share_dir():
    cmd = "rm -rf %s/*" % SHARE_SHEEP_DIR
    local(cmd, capture=True)


def start_sheep_cluster():
    # start corosync service in each sheepdog containers
    print "start corosync service in each sheepdog containers"
    for sheep in SHEEP:
        e_command = "service corosync start"
        cmd = "docker exec %s %s" % (sheep["name"], e_command)
        local(cmd, capture=True)
    print "wait corosync ..."
    time.sleep(3)

    # start sheepdog service in each sheepdog containers
    print "start sheepdog service in each sheepdog containers"
    for sheep in SHEEP:
        e_command = "sheep -b %s -p 7000 -y %s -i host=%s,port=7001 -c corosync /var/lib/sheepdog/%s"\
                    % (sheep["addr"], sheep["addr"], sheep["addr"], sheep["name"])
        cmd = "docker exec %s %s" % (sheep["name"], e_command)
        local(cmd, capture=True)
    print "wait sheepdog ..."
    time.sleep(3)

    sheep_head = SHEEP[0]

    # start tgtd service in sheepdog head
    print "start tgtd service in sheepdog head"
    e_command = "service tgtd start"
    cmd = "docker exec %s %s" % (sheep_head["name"], e_command)
    local(cmd, capture=True)
    print "wait tgtd ..."
    time.sleep(3)

    # execute cluster format in sheepdog cluster
    print "execute cluster format in sheepdog cluster"
    e_command = "dog cluster format --copies=3 -a %s" % (sheep_head["addr"])
    cmd = "docker exec %s %s" % (sheep_head["name"], e_command)
    local(cmd, capture=True)

    # create vdi
    print "create vdi"
    e_command = "dog vdi create %s %s -a %s" % (VDI["name"], VDI["size"], sheep_head["addr"])
    cmd = "docker exec %s %s" % (sheep_head["name"], e_command)
    local(cmd, capture=True)

    # setting target
    print "setting target"
    e_command = "tgtadm --lld iscsi --mode=target --op new --tid=1 --targetname jp.co.strage.%s" % (VDI["name"])
    cmd = "docker exec %s %s" % (sheep_head["name"], e_command)
    local(cmd, capture=True)

    # setting logicalunit
    print "setting target"
    e_command = "tgtadm --mode logicalunit --op new --tid=1 --lun=1 --bstype sheepdog" \
                " --backing-store unix:/var/lib/sheepdog/%s/sock:%s" % (sheep_head["name"], VDI["name"])
    cmd = "docker exec %s %s" % (sheep_head["name"], e_command)
    local(cmd, capture=True)

    # bind target
    print "bind target"
    e_command = "tgtadm --mode target --op bind --tid=1 --initiator-address ALL"
    cmd = "docker exec %s %s" % (sheep_head["name"], e_command)
    local(cmd, capture=True)


def check_posdog_environment():
    env_exists = False
    if check_bridge() or check_container() or check_share_dir():
        env_exists = True
    return env_exists


def create_posdog_environment():

    # initial environment for postgres and sheepdog
    if check_posdog_environment():
        return False
    # create share directory
    make_share_dir()
    # create bridge
    create_bridge()
    # run sheepdog on docker container
    for sheepdog in SHEEP:
        run_container(sheepdog)
    # run postgres on docker container
    postgres = POS[0]
    run_container(postgres)

    # start sheepdog cluster
    start_sheep_cluster()

    return True


def destroy_posdog_environment():
    containers = get_container()
    for container in containers:
        container_name = container.split()[-1]
        for pos in POS:
            if pos["name"] == container_name:
                stop_container(container_name)
        for sheep in SHEEP:
            if sheep["name"] == container_name:
                stop_container(container_name)
    destroy_bridge()
    delete_share_dir()

