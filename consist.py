# -*-coding:utf8-*-

# -- machine_manager db config
MACHINE_MANAGER_DB_HOST = "10.101.1.140"
MACHINE_MANAGER_DB_PORT = 3306
MACHINE_MANAGER_DB_USER = "worker"
MACHINE_MANAGER_DB_PASSWD = "services"
MACHINE_MANAGER_DB_NAME = "MachineToolManageDB"

# -- dashboard_db_config --
DASHBOARD_DB_HOST = "10.101.2.35"
DASHBOARD_DB_PORT = 3306
DASHBOARD_DB_USER = "falcon"
DASHBOARD_DB_PASSWD = "0facd04df46c907a"
DASHBOARD_DB_NAME = "dashboard"


#-- graph db config --
GRAPH_DB_HOST = "10.101.2.35"
GRAPH_DB_PORT = 3306
GRAPH_DB_USER = "falcon"
GRAPH_DB_PASSWD = "0facd04df46c907a"
GRAPH_DB_NAME = "graph"


# -- falcon_portal_db config--
FALCON_PORTAL_DB_HOST = "10.101.2.35"
FALCON_PORTAL_DB_PORT = 3306
FALCON_PORTAL_DB_USER = "falcon"
FALCON_PORTAL_DB_PASSWD = "0facd04df46c907a"
FALCON_PORTAL_DB_NAME = "falcon_portal"


BASE_COUNTERS = "load.1min|load.5min|cpu.user|cpu.system|cpu.idle|mem.memfree.percent|cpu.iowait|ss.estab|ss.timewait"
NET_COUNTERS = "metric=net.if.in.bytes|metric=net.if.out.bytes"
DISK_COUNTERS = "metric=df.bytes.free.percent"

TITLE_BASE = "base"
TITLE_NET = "net"
TITLE_DISK = "disk"

ROOT_NAME = "基础监控_测试"
REDIS_HEAD = "ops:zhangkun:"