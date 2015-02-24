import os
import time
from fabric.api import local

BRIDGE1 = {"name": "br0", "idx": "1", "addr": "10.0.10.254", "mask": "/24"}
BRIDGE2 = {"name": "br1", "idx": "2", "addr": "10.0.11.254", "mask": "/24"}
POS1 = {"name": "postgres1", "addr": "10.0.10.1", "image": "nhanaue/postgres"}
POS2 = {"name": "monitor", "addr": "10.0.10.2", "image": "nhanaue/postgres"}
SHEEP1 = {"name": "sheepdog1", "addr": "10.0.10.11", "addr_b": "10.0.11.11", "image": "nhanaue/sheepdog"}
SHEEP2 = {"name": "sheepdog2", "addr": "10.0.10.12", "addr_b": "10.0.11.12", "image": "nhanaue/sheepdog"}
SHEEP3 = {"name": "sheepdog3", "addr": "10.0.10.13", "addr_b": "10.0.11.12", "image": "nhanaue/sheepdog"}
BRIDGE = [BRIDGE1, BRIDGE2]
POS = [POS1, POS2]
SHEEP = [SHEEP1, SHEEP2, SHEEP3]

VDI = {"name": "vdipos", "size": "10G"}
SHARE_SHEEP_DIR = "/var/lib/sheepdog"
SHARE_POS_DIR = "/mnt/postgres"
PG_STARTUP_FILE = "pg_startup.sh"
WAIT_TIME = 3


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
    local("apt-get install -y --force-yes open-iscsi", capture=True)
    local("wget https://raw.github.com/jpetazzo/pipework/master/pipework -O /usr/local/bin/pipework",
          capture=True)
    local("chmod 755 /usr/local/bin/pipework", capture=True)
    # pull docker images
    local("docker pull nhanaue/sheepdog", capture=True)
    local("docker pull nhanaue/postgres", capture=True)


def check_bridge():
    for bridge in BRIDGE:
        sysfs_name = "/sys/class/net/" + bridge["name"]
        if os.path.exists(sysfs_name):
            r_bridge = (False, "bridge is already settings.")
            return r_bridge
    r_bridge = (True, "bridge is not settings.")
    return r_bridge


def create_bridge():
    for bridge in BRIDGE:
        cmd = "brctl addbr " + bridge["name"]
        local(cmd, capture=True)
        cmd = "ifconfig " + bridge["name"] + " " + bridge["addr"]
        local(cmd, capture=True)
        cmd = "ifconfig " + bridge["name"] + " up"
        local(cmd, capture=True)


def destroy_bridge():
    for bridge in BRIDGE:
        sysfs_name = "/sys/class/net/" + bridge["name"]
        if os.path.exists(sysfs_name):
            cmd = "ifconfig " + bridge["name"] + " down"
            local(cmd, capture=True)
            cmd = "brctl delbr " + bridge["name"]
            local(cmd, capture=True)


def set_ipaddr(name, addr, bridge):
    addr += "/24"
    cmd = "pipework %s -i eth%s %s %s" % (bridge["name"], bridge["idx"], name, addr)
    local(cmd, capture=True)


def check_container():
    outbuf = local("docker ps -a", capture=True)
    docker_ps = outbuf.split('\n')
    for container in docker_ps:
        container_name = container.split()[-1]
        for pos in POS:
            if pos["name"] == container_name:
                r_container = (False, "posgres container is already exists.")
                return r_container
        for sheep in SHEEP:
            if sheep["name"] == container_name:
                r_container = (False, "sheepdog container is already exists.")
                return r_container
    r_container = (True, "sheepdog container is not exists.")
    return r_container


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
    if "sheepdog" in instans["name"]:
        cmd = "docker run --privileged=true --name %s -v %s:%s -id %s" \
            % (instans["name"], SHARE_SHEEP_DIR, SHARE_SHEEP_DIR, instans["image"])
        local(cmd, capture=True)
        set_ipaddr(instans["name"], instans["addr"], BRIDGE1)
        set_ipaddr(instans["name"], instans["addr_b"], BRIDGE2)
    else:
        cmd = "docker run --privileged=true --name %s -v %s:%s -id %s"\
              % (instans["name"], SHARE_POS_DIR, SHARE_POS_DIR, instans["image"])
        local(cmd, capture=True)
        set_ipaddr(instans["name"], instans["addr"], BRIDGE1)


def stop_container(name):
    cmd = "docker rm -f " + name
    local(cmd, capture=True)


def check_share_dir():
    for sheep in SHEEP:
        dir = "%s/%s" % (SHARE_SHEEP_DIR, sheep["name"])
        if os.path.exists(dir):
            r_dir = (False, "shared sheepdog dir is already exists.")
            return r_dir
    if os.path.exists(SHARE_POS_DIR):
        r_dir = (False, "shared postgres dir is already exists.")
        return r_dir
    r_dir = (True, "shared postgres dir is not exists.")
    return r_dir


def make_share_dir():
    for sheep in SHEEP:
        cmd = "mkdir %s/%s" % (SHARE_SHEEP_DIR, sheep["name"])
        local(cmd, capture=True)


def make_mnt_dir_for_postgres():
    cmd = "mkdir %s" % SHARE_POS_DIR
    local(cmd, capture=True)


def delete_share_dir():
    cmd = "rm -rf %s/*" % SHARE_SHEEP_DIR
    local(cmd, capture=True)
    cmd = "rm -rf %s" % SHARE_POS_DIR
    local(cmd, capture=True)


def check_iscsi_session():
    target_vdi = "jp.co.strage.%s" % VDI["name"]
    cmd = 'echo `iscsiadm -m session --show`'
    sessions = local(cmd, capture=True)

    if target_vdi in sessions:
        connected = (False, "iscsi sessions this already connected.")
        return connected
    connected = (True, "iscsi sessions this not connected.")
    return connected


def connect_iscsi_session():
    target_vdi = "jp.co.strage.%s" % VDI["name"]
    cmd = "iscsiadm -m discovery --type sendtargets -p %s" % SHEEP1["addr"]
    local(cmd, capture=True)
    cmd = "iscsiadm -m node -T %s --login" % target_vdi
    local(cmd, capture=True)


def disconnect_iscsi_session():
    if check_iscsi_session()[0] is False:
        target_vdi = "jp.co.strage.%s" % VDI["name"]
        cmd = "iscsiadm -m node -T %s --logout" % target_vdi
        local(cmd, capture=True)


def check_device():
    # check device
    loaded_device = False
    device_dir = "/dev/disk/by-path"
    if os.path.exists(device_dir):
        loaded_device = True
    return loaded_device


def make_filesystem():
    # check file system
    if check_device() is False:
        err = "not found device [ /dev/disk/by-path/~]"
        r_make = (False, err)
        return r_make
    cmd = "echo `ls -l  /dev/disk/by-path/ip-* | awk -F'/' '{print $NF}'`"
    device = local(cmd, capture=True)
    print "making file system please wiat..."
    cmd = "parted -s -a optimal /dev/%s mklabel gpt -- mkpart primary ext4 1 -1" % str(device)
    local(cmd, capture=True)
    target_partision = "%s1" % str(device)
    cmd = "mkfs.ext4 /dev/%s" % target_partision
    local(cmd, capture=True)
    r_make = (True, target_partision)
    return r_make


def mount_dick_on_sheepdog_vdi():
    connect_iscsi_session()
    print "wait for iscsi connection"
    time.sleep(WAIT_TIME)
    r_make = make_filesystem()
    if r_make[0] is False:
        return r_make
    cmd = "mount /dev/%s %s" % (r_make[1], SHARE_POS_DIR)
    local(cmd, capture=True)
    r_mnt = (True, "")
    return r_mnt


def umount_dick_on_sheepdog_vdi():
    cmd = "echo `df -h`"
    mnt_dirs = local(cmd, capture=True)
    if SHARE_POS_DIR in mnt_dirs:
        cmd = "umount %s" % SHARE_POS_DIR
        local(cmd, capture=True)


def make_pg_startup_file():
    cmd = "cp ./%s %s/" % (PG_STARTUP_FILE, SHARE_POS_DIR)
    local(cmd, capture=True)
    cmd = "chmod 755 %s/%s" % (SHARE_POS_DIR, PG_STARTUP_FILE)
    local(cmd, capture=True)


def start_sheep_cluster():
    # start corosync service in each sheepdog containers
    print "start corosync service in each sheepdog containers"
    for sheep in SHEEP:
        e_command = "service corosync start"
        cmd = "docker exec %s %s" % (sheep["name"], e_command)
        local(cmd, capture=True)
    print "wait for corosync ..."
    time.sleep(WAIT_TIME)

    # start sheepdog service in each sheepdog containers
    print "start sheepdog service in each sheepdog containers"
    for sheep in SHEEP:
        e_command = "sheep -b %s -p 7000 -y %s -i host=%s,port=7001 -c corosync /var/lib/sheepdog/%s"\
                    % (sheep["addr"], sheep["addr"], sheep["addr_b"], sheep["name"])
        cmd = "docker exec %s %s" % (sheep["name"], e_command)
        local(cmd, capture=True)
    print "wait for sheepdog ..."
    time.sleep(WAIT_TIME)

    sheep_head = SHEEP[0]

    # start tgtd service in sheepdog head
    print "start tgtd service in sheepdog head"
    e_command = "service tgtd start"
    cmd = "docker exec %s %s" % (sheep_head["name"], e_command)
    local(cmd, capture=True)
    print "wait for tgtd ..."
    time.sleep(WAIT_TIME)

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


def start_postgres():
    cmd = "docker exec %s %s/%s > /mnt/postgres/startup.log 2>&1 &" % (POS1["name"], SHARE_POS_DIR, PG_STARTUP_FILE)
    local(cmd, capture=True)


def check_posdog_environment():
    r_iscsi = check_iscsi_session()
    if r_iscsi[0] is False:
        return r_iscsi
    r_container = check_container()
    if r_container[0] is False:
        return r_container
    r_share = check_share_dir()
    if r_share[0] is False:
        return r_share
    r_bridge = check_bridge()
    if r_bridge[0] is False:
        return r_bridge
    r_check = (True, "")
    return r_check


def create_posdog_environment():
    # initial environment for postgres and sheepdog
    print "####################################################################################"
    print "###   Advance preparation of environment                                         ###"
    print "####################################################################################"
    r_check = check_posdog_environment()
    if r_check[0] is False:
        return r_check

    make_share_dir()
    make_mnt_dir_for_postgres()
    create_bridge()

    print "####################################################################################"
    print "###   Initialization of sheepdog cluster                                         ###"
    print "####################################################################################"
    # run sheepdog on docker container
    for sheepdog in SHEEP:
        run_container(sheepdog)

    # start sheepdog cluster
    start_sheep_cluster()

    print "####################################################################################"
    print "###   Initialization of Postgres                                                 ###"
    print "####################################################################################"
    # mount disk on sheepdog vdi
    r_mnt = mount_dick_on_sheepdog_vdi()
    if r_mnt[0] is False:
        return r_mnt
    # run postgres on docker container
    postgres = POS[0]
    run_container(postgres)

    # start postgres service
    make_pg_startup_file()
    start_postgres()
    r_create = (True, "")
    return r_create


def destroy_posdog_environment():
    containers = get_container()
    for container in containers:
        container_name = container.split()[-1]
        for pos in POS:
            if pos["name"] == container_name:
                stop_container(container_name)

    umount_dick_on_sheepdog_vdi()
    disconnect_iscsi_session()

    for container in containers:
        container_name = container.split()[-1]
        for sheep in SHEEP:
            if sheep["name"] == container_name:
                stop_container(container_name)
    delete_share_dir()
    destroy_bridge()


