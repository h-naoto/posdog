import control as cl
from optparse import OptionParser, OptionValueError


def op_parse():
    usage = "usage: %prog [options] keyword"
    parser = OptionParser(usage)
    parser.add_option(
        "-t", "--task",
        type="choice",
        choices=["install", "create", "destroy"],
        default="create",
        dest="task",
        help="meaningless option"
    )

    return parser


def main():
    if cl.check_user() is False:
        print "Please running in root."
        return

    parser = op_parse()
    (options, args) = parser.parse_args()

    task = options.task
    if task == "install":
        cl.install_docker_and_tools()
    elif task == "create":
        r_create = cl.create_posdog_environment()
        if r_create[0] is False:
            print r_create[1]
            print "execute [python posdog.py -t destroy] command."

    elif task == "destroy":
        cl.destroy_posdog_environment()
    else:
        print "invalid option"

if __name__ == "__main__":
    main()