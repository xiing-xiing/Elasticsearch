#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging
import os
import random
import subprocess
import sys
import time
import datetime

if sys.getdefaultencoding() != 'utf-8':
    reload(sys)
    sys.setdefaultencoding('utf-8')

logfile = "log_" + os.path.basename(sys.argv[0]).split(".")[0].split(".")[0] + ".log"
working_path = sys.path[0] + os.path.sep
log_path = "./"

log_level = logging.DEBUG

# 检查zk集群状态
zk_ips = []
zk_port = 2181
zoo_conf = "{zk部署目录}/conf/zoo.cfg"

def getlogger(name, path_file_name):
    logger = logging.getLogger(name)
    if len(logger.handlers) == 0:
        logger.setLevel(log_level)
        fh = logging.FileHandler(path_file_name, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        if name != "file":
            console = logging.StreamHandler()
            console.setLevel(log_level)
            formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
            console.setFormatter(formatter)
            logger.addHandler(console)
    return logger


if not os.path.exists(log_path):
    os.makedirs(log_path)

logger = getlogger("default", log_path + logfile)
file_logger = getlogger("file", log_path + logfile)


def run_shell(cmd, stderr2out=True):
    p = None
    if stderr2out:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, stderr=subprocess.STDOUT)
    else:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    out, err = p.communicate()
    if logger:
        logger.debug('running:%s,output:\n%s' % (cmd, out))
    return p.returncode, out


def get_zoo_server_list(conf_path):
    server_list = []
    (status, output) = run_shell("cat " + zoo_conf)
    if status != 0:
        return server_list
    lines = output.split("\n")
    for line in lines:
        if "server." in line and "#" not in line:
            tmp = line.split("=")
            if len(tmp) != 2:
                continue
            host = tmp[1].split(":")[0]
            server_list.append(host)
    return server_list


def main():
    result = []
    all_ips = []
    all_ips = get_zoo_server_list(zoo_conf)
    all_ips = all_ips + zk_ips
    for ip in all_ips:
        (status, output) = run_shell("echo mntr|nc -w 3 " + ip + " " + str(zk_port))
        ip_result = {"conn": ip + ":" + str(zk_port), "result": None, "server_state": None}
        if status != 0:
            ip_result["result"] = "dead:conn " + ip + ":" + str(zk_port) + " failed."
        else:
            server_info = output.split("\n")
            for info in server_info:
                if "zk_server_state" in info:
                    ip_result["server_state"] = info.split("\t")[-1]

            if ip_result["server_state"] is None:
                ip_result["result"] = "dead:zk role failed."
            else:
                ip_result["result"] = "alive"
        result.append(ip_result)

    # 输出结果
    print("=================result=================")
    for ip_result in result:
        print(json.dumps(ip_result))

    if len(all_ips) == 0:
        print("get server empty from " + zoo_conf + ",and zk_ips empty.")


if __name__ == '__main__':
    main()
