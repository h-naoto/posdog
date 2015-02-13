import os
from fabric.api import local

BRIDGE = {"name": "br0", "addr": "192.168.10.254", "mask": "/24"}
POS_ADDR1 = "192.168.10.1"
POS_ADDR2 = "192.168.10.2"
SHEEP_ADDR1 = "192.168.10.11"
SHEEP_ADDR2 = "192.168.10.12"
SHEEP_ADDR3 = "192.168.10.13"
POS_ADDRS = [POS_ADDR1, POS_ADDR2]
SHEEP_ADDS = [SHEEP_ADDR1, SHEEP_ADDR2, SHEEP_ADDR3]

SHARE_DIR = "/tmp/posdog"

def test_user_check():
    root = False
    outbuf = local("echo $USER", capture=True)
    user = outbuf
    if user == "root":
        root = True

    return root


def install_docker_and_tools():
    print "start install packages of test environment."
    if test_user_check() is False:
        print "you are not root"
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
    local("apt-get install -y --force-yes tcpdump", capture=True)
    local("apt-get install -y --force-yes lv", capture=True)
    local("wget https://raw.github.com/jpetazzo/pipework/master/pipework -O /usr/local/bin/pipework",
          capture=True)
    local("chmod 755 /usr/local/bin/pipework", capture=True)
    # pull docker images
    local("docker pull nhanaue/sheepdog", capture=True)
    local("docker pull nhanaue/postgres", capture=True)


def bridge_setting_check():
    setting_exists = False
    sysfs_name = "/sys/class/net/" + BRIDGE["name"]
    if os.path.exists(sysfs_name):
        setting_exists = True
        return setting_exists
    return setting_exists


def docker_container_set_ipaddr(name, addr):
    cmd = "pipework %s %s %s" % (BRIDGE["name"], name, addr)
    local(cmd, capture=True)


def docker_container_run(name, addr):
    image_name = "nhanaue/%s" % name
    cmd = "docker run --privileged=true -v %s:/root/share_volume --name %s -id %s" % (SHARE_DIR, name, image_name)
    local(cmd, capture=True)
    docker_container_set_ipaddr(name, addr)