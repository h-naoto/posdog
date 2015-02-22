import os
import time
import controller as co
from fabric.api import local


def check_monitor_environment():
    outbuf = local("docker ps -a", capture=True)
    docker_ps = outbuf.split('\n')
    for container in docker_ps:
        container_name = container.split()[-1]
        if co.POS2["name"] == container_name:
            r_container = (True, "monitor container is already exists.")
            return r_container
    r_container = (False, "")
    return r_container


def check_posdog_environment():
    r_bridge = co.check_bridge()
    if r_bridge[0]:
        return r_bridge
    r_share = co.check_share_dir()
    if r_share[0]:
        return r_share
    r_container = co.check_container()
    if r_container[0]:
        return r_container
    r_iscsi = co.check_iscsi_session()
    print "check1" + str(r_iscsi[0])
    if r_iscsi[0]:
        print "check2" + str(r_iscsi[0])
        return r_iscsi
    r_check = (False, "")
    return r_check


def create_monitoring_environment():
    # initial environment for postgres and sheepdog

    r_check_p = check_posdog_environment()
    print "after check3" + str(r_check_p[0])
    if r_check_p[0]:
        return r_check_p
    r_check_m = check_monitor_environment()
    if r_check_m[0]:
        return r_check_m

    # run monitor container
    monitor = co.POS2
    print "start monitor container"
    co.run_container(monitor)

    r_monitor = (False, "")
    return r_monitor