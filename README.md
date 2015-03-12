Posdog
========================
Posdog using postgreSQL and Sheepdog and docker
All of postgreSQL and sheepdog process runs on docker, and postgreSQL to provide a database
system to use a sheepdog Cluster.

Preparation
-----------
Please set up Ubuntu 14.04 Server Edition,
and use in a proxy-free environment

Setup
-----
Execute the following commands on a python inside the virtual machine or physical machine:

install the python packages and libraries required to run the test program
and clone posdog repository.
```
% sudo apt-get install python-pip
% sudo apt-get install python-dev
% sudo git clone https://github.com/h-naoto/posdog.git
% sudo cd ./posdog
% sudo pip install -r pip-requires.txt

```


This step installs other packages such as Docker container and generates some helper scripts
needed by the posdog.
```
% sudo python posdog.py -t install

```

Please make sure following packages are installed properly inside the machine.

 * docker
 * bridge-utils
 * pipework
 * open-iscsi
 * iputils-arping
 * lv


Start
-----
Please run the environment build script as root.

 * posdog.py is environment operate script.
```
% sudo python posdog.py [ -t <options> ]


```

After the script, postgreSQL and sheepdog of environment that runs on docker would be built.

Options
-----
 * use [ -t install  ]
   This option is install the packages required for posdog.
 * use [ -t create   ]
   This option is create the posdog environment.
 * use [ -t destroy  ]
   This option is destroy the posdog environment.
 * use [ -t recreate ]
   This option is recreate the posdog environment.
   once you create by breaking the environment again.
 * use [ -t monitor  ]
   This option is create container for monitoring postgreSQL process,
   and failover the postgresSQL.
   

Examples
-----
 How to use [ -t install  ] option
```
% sudo python posdog.py -t install

```

 How to use [ -t create  ] option
```
% sudo python posdog.py -t create

```

 How to use [ -t monitor  ] option
```
% sudo python posdog.py -t monitor

```

 How to use [ -t recreate  ] option
```
% sudo python posdog.py -t recreate

```

 How to use [ -t destroy  ] option
```
% sudo python posdog.py -t destroy

```