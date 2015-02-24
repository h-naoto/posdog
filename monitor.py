import os
import time
import controller as co
from fabric.api import local


def check_container_environment(instance):
    outbuf = local("docker ps -a", capture=True)
    docker_ps = outbuf.split('\n')
    for container in docker_ps:
        container_name = container.split()[-1]
        if instance["name"] == container_name:
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


# restart postgres
def restart_postgres():
    r_check_p = check_container_environment(co.POS1)
    if r_check_p[0]:
        # stop postgres docker container
        co.stop_container(co.POS1["name"])
    # run postgres docker container
    postgres = co.POS[0]
    co.run_container(postgres)
    # start postgres service
    co.make_pg_startup_file()
    co.start_postgres()


def monitor_postgres():
    while True:
        cmd = "echo `ps ax | grep postgres: | grep -v grep`"
        pg_state = local(cmd, capture=True)
        if "postgres" not in pg_state:
            print "####################################################################################"
            print "###   Postgres process is dead and try to restart                                ###"
            print "####################################################################################"
            restart_postgres()
        else:
            cmd = 'docker exec monitor /usr/local/pgsql/bin/psql -h 10.0.10.1 -U postgres -c "select now()"'
            pg_resp = local(cmd, capture=True)
            if "1 row" in pg_resp:
                print pg_resp
            else:
                print "####################################################################################"
                print "###   postgres is no response and try to restart                                ###"
                print "####################################################################################"
                print pg_resp
                restart_postgres()
        time.sleep(co.WAIT_TIME)


def create_monitoring_environment():
    # initial environment for postgres and sheepdog

    r_check_p = check_posdog_environment()
    if r_check_p[0]:
        return r_check_p
    r_check_m = check_container_environment(co.POS2)
    if r_check_m[0]:
        # stop postgres docker container
        print r_check_m[1]
        co.stop_container(co.POS2["name"])

    # run monitor container
    monitor = co.POS2
    print "start monitor container"
    co.run_container(monitor)

    monitor_postgres()

    r_monitor = (False, "")
    return r_monitor