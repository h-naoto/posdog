import controller as co
import monitor as mo
from optparse import OptionParser


def op_parse():
    usage = "usage: %prog [options] keyword"
    parser = OptionParser(usage)
    parser.add_option(
        "-t", "--task",
        type="choice",
        choices=["install", "create", "recreate", "monitor", "destroy"],
        default="create",
        dest="task",
        help="meaningless option"
    )

    return parser


def main():
    if co.check_user() is False:
        print "Please running in root."
        return

    parser = op_parse()
    (options, args) = parser.parse_args()

    task = options.task
    if task == "install":
        co.install_docker_and_tools()

    elif task == "create":
        r_create = co.create_posdog_environment()
        if r_create[0] is False:
            print "ERROR: %s" % r_create[1]
            print "execute [python posdog.py -t destroy] command."

    elif task == "recreate":
        co.destroy_posdog_environment()
        r_create = co.create_posdog_environment()
        if r_create[0] is False:
            print "ERROR: %s" % r_create[1]
            print "execute [python posdog.py -t destroy] command."

    elif task == "monitor":
        r_create = mo.create_monitoring_environment()
        if r_create[0]:
            print "ERROR: %s" % r_create[1]

    elif task == "destroy":
        co.destroy_posdog_environment()

    else:
        print "invalid option"

if __name__ == "__main__":
    main()