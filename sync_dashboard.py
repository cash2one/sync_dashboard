# -*-coding:utf8-*-
import consist
import redis
import time

from DB import DB
from logger import log


def get_namespace(mm_conn, id, path):
    cursor = mm_conn.execute("select des,parent from namespace where namespace_id=%s", (id,))
    result = cursor.fetchone()
    cursor and cursor.close()

    if result:
        path.insert(0, result[0])
        get_namespace(mm_conn, result[1], path)


def get_hostname_by_namespace(mm_conn, fp_conn):
    log.info("begin to get hostname by namespace")

    list_namespace_hostname = []

    cursor = mm_conn.execute("select namespace_id from namespace where type = 'leaf' ")
    leafnodes = cursor.fetchall()
    cursor and cursor.close()

    for leaf in leafnodes:
        path = []
        tmp_dict = {}

        cursor = mm_conn.execute("select machine_IP from instance i join namespace_machine_relation n "
                                  "on i.machine_id=n.machine_id where n.namespace = %s", (leaf[0],))
        machine = cursor.fetchall()
        cursor and cursor.close()

        tmp_hostname = []
        for machine_ip in machine:
            cursor = fp_conn.execute("select hostname from host where ip=%s", (machine_ip[0],))
            exist = cursor.fetchone()
            if exist:
                tmp_hostname.append(exist[0])

        if not len(tmp_hostname):
            continue

        get_namespace(mm_conn, leaf[0], path)

        tmp_dict['hostname'] = '|'.join(tmp_hostname)
        tmp_dict['namespace'] = '/'.join(path)

        list_namespace_hostname.append(tmp_dict)

    return list_namespace_hostname


def get_id(db_conn, name):
    '''
    get the  namespace's id
    :param name: name in table dashboard_screen
    :return: the id of the name or None
    '''
    cursor = db_conn.execute('''select id from dashboard_screen where name=%s''', (name,))
    id = cursor.fetchone()
    cursor and cursor.close()

    if id is not None:
        return id[0]
    else:
        return None


def if_screen_exist(db_conn, pid, name):
    '''
    judge if the screen is exist,if exist,return id,or return None
    :param pid:pid in table dashboard_screen
    :param name:name in table dashboard_screen
    :return:the id of the screen or None
    '''

    cursor = db_conn.execute("select id from  dashboard_screen where pid = %s and name = %s", (pid, name))
    exist = cursor.fetchone()
    cursor and cursor.close()

    if exist:
        return exist[0]
    else:
        return None


def if_graph_exist(db_conn, screen_id, title):
    '''
    judge if graph is exist,if exist return id or return None
    :param screen_id:
    :param title:
    :return:
    '''
    cursor = db_conn.execute("select id from  dashboard_graph where screen_id = %s and title = %s", (screen_id, title))
    exist = cursor.fetchone()
    cursor and cursor.close()

    if exist:
        return exist[0]
    else:
        return None


def need_update(db_conn, id, hosts, counters):
    cursor = db_conn.execute("select hosts,counters from dashboard_graph where id = %s",(id,))
    result = cursor.fetchone()
    cursor and cursor.close()
    if result:
        if result[0] == hosts and result[1] == counters:
            return False

    return True


def add_screen(db_conn, pid, name):
    '''
    if screen not exist,add it and return the new id
    :param pid:
    :param name:
    :return:
    '''
    cursor = db_conn.execute("insert into dashboard_screen (pid, name) values(%s,%s)", (pid, name))
    screen_id = cursor.lastrowid
    db_conn.commit()
    cursor and cursor.close()

    return screen_id


def update_graph(db_conn, id, hosts, counters):
    '''
    update the graph in dashboard_graph
    :param id:
    :param hosts:
    :param counters:
    :return:
    '''
    cursor = db_conn.execute('''update dashboard_graph set  hosts=%s, counters=%s where id = %s''', (hosts, counters, id))
    db_conn.commit()
    cursor and cursor.close()


def add_graph(db_conn, title, hosts, counters, screen_id, timespan=3600, graph_type='h', method='', position=0):

    cursor = db_conn.execute('''insert into dashboard_graph (title, hosts, counters, screen_id,
                            timespan, graph_type, method, position)
                            values(%s, %s, %s, %s, %s, %s, %s, %s)''',
                            (title, hosts or "", counters or "",
                            screen_id, timespan, graph_type, method, position))
    graph_id = cursor.lastrowid

    db_conn.execute('''update dashboard_graph set position=%s where id=%s''', (graph_id, graph_id))
    db_conn.commit()
    cursor and cursor.close()

    return graph_id


def sync_dashboard(sync_redis, mm_conn, db_conn, fp_conn):
    log.info("sync_dashboard start")

    list_namespace_hostname = get_hostname_by_namespace(mm_conn, fp_conn)

    if not len(list_namespace_hostname):
        log.error("namespace and hostname info is null,stop sync")
        return

    pid = get_id(db_conn, consist.ROOT_NAME)

    if pid is None:
        log.error("there is no root namespace:%s,now add it" % consist.ROOT_NAME)
        pid = add_screen(db_conn, 0, consist.ROOT_NAME)

    if pid is None:
        log.error("add screen error,stop sync")
        return

    log.info("start to sync namespace info to dashboard")

    for m in list_namespace_hostname:
        namespace = m['namespace']

        exist = sync_redis.hget(consist.REDIS_HEAD+str(pid), namespace)  # if namespace exist in redis
        if exist:
            screen_id = exist #get screen_id from redis
        else:
            log.debug("pid:%s,namespace:%s is not exist in redis,now try to find it from db" % (pid, namespace))
            exist = if_screen_exist(db_conn, pid, namespace)  # namespace is not exist in redis,try to find it in db
            if exist:
                screen_id = exist
                log.debug("pid:%s,namespace:%s is not exist in redis but in db" % (pid, namespace))
            else:
                log.info("pid:%s,namespace:%s is not exist,add it" % (pid, namespace))
                screen_id = add_screen(db_conn, pid, namespace)  # not in redis and db ,add it

            if screen_id is None:
                log.error("add screen error,stop sync")
                return

            sync_redis.hset(consist.REDIS_HEAD+str(pid), namespace, screen_id)  # update redis
            log.info('screen not in redis, add it:key:%s,namespace:%s,value:%s' % (consist.REDIS_HEAD+str(pid), namespace, screen_id))

        str_hostnames = m['hostname']

        #  base graph
        exist = sync_redis.hget(consist.REDIS_HEAD+str(screen_id), consist.TITLE_BASE)
        if exist:
            if need_update(db_conn, exist, str_hostnames, consist.BASE_COUNTERS):
                update_graph(db_conn, exist, str_hostnames, consist.BASE_COUNTERS)
                log.info("graph exist in redis, update it:graphid:%s,title:%s,hosts:%s" % (exist, consist.TITLE_BASE, str_hostnames))
        else:
            exist = if_graph_exist(db_conn, screen_id, consist.TITLE_BASE)

            if exist:
                graph_id = exist
                if need_update(db_conn, exist, str_hostnames, consist.BASE_COUNTERS):
                    update_graph(db_conn, exist, str_hostnames, consist.BASE_COUNTERS)
                    log.info("graph exist in db,update it:graphid:%s,title:%s,hosts:%s" % (exist, consist.TITLE_BASE, str_hostnames))
            else:
                graph_id = add_graph(db_conn, consist.TITLE_BASE, str_hostnames, consist.BASE_COUNTERS, screen_id)
                log.info("graph is not exist,add it:screen_id:%s,title:%s,value:%s" % (screen_id, consist.TITLE_BASE, graph_id))

            sync_redis.hset(consist.REDIS_HEAD+str(screen_id), consist.TITLE_BASE, graph_id)
            log.info("set graph in redis:screen_id:%s,title:%s,value:%s" % (consist.REDIS_HEAD+str(screen_id), consist.TITLE_BASE, graph_id))

        # net graph
        exist = sync_redis.hget(consist.REDIS_HEAD + str(screen_id), consist.TITLE_NET)
        if exist:
            if need_update(db_conn, exist, str_hostnames, consist.NET_COUNTERS):
                update_graph(db_conn, exist, str_hostnames, consist.NET_COUNTERS)
                log.info("graph exist in redis,update it:graphid:%s,title:%s,hosts:%s" % (exist, consist.TITLE_NET, str_hostnames))
        else:
            exist = if_graph_exist(db_conn, screen_id, consist.TITLE_NET)

            if exist:
                graph_id = exist
                if need_update(db_conn, exist, str_hostnames, consist.NET_COUNTERS):
                    update_graph(db_conn, exist, str_hostnames, consist.NET_COUNTERS)
                    log.info("graph exist in db, update it:graphid:%s,title:%s, hosts:%s" % (exist, consist.TITLE_NET, str_hostnames))
            else:
                graph_id = add_graph(db_conn, consist.TITLE_NET, str_hostnames, consist.NET_COUNTERS, screen_id)
                log.info("graph is not exist,add it:screen_id:%s,title:%s,value:%s" % (screen_id, consist.TITLE_NET, graph_id))

            sync_redis.hset(consist.REDIS_HEAD + str(screen_id), consist.TITLE_NET, graph_id)

            log.info("set graph in redis:screen_id:%s,title:%s,value:%s" % (consist.REDIS_HEAD + str(screen_id), consist.TITLE_NET, graph_id))

        # disk graph
        exist = sync_redis.hget(consist.REDIS_HEAD + str(screen_id), consist.TITLE_DISK)
        if exist:
            if need_update(db_conn, exist, str_hostnames, consist.DISK_COUNTERS):
                update_graph(db_conn, exist, str_hostnames, consist.DISK_COUNTERS)
                log.info("graph exist in redis,update it:graphid:%s,title:%s,hosts:%s" % (exist, consist.TITLE_DISK, str_hostnames))
        else:
            exist = if_graph_exist(db_conn, screen_id, consist.TITLE_DISK)

            if exist:
                graph_id = exist
                if need_update(db_conn, exist, str_hostnames, consist.DISK_COUNTERS):
                    update_graph(db_conn, exist, str_hostnames, consist.DISK_COUNTERS)
                    log.info("graph exist in db, update it:screen_id:%s,title:%s,hosts:%s" % (screen_id, consist.TITLE_DISK, str_hostnames))
            else:
                graph_id = add_graph(db_conn, consist.TITLE_DISK, str_hostnames, consist.DISK_COUNTERS, screen_id)
                log.info("add graph,scree_id:%s,title:%s,value:%s" % (screen_id, consist.TITLE_DISK, graph_id))

            sync_redis.hset(consist.REDIS_HEAD + str(screen_id), consist.TITLE_DISK, graph_id)
            log.info("set graph redis:screen_id:%s,title:%s,value:%s" % (consist.REDIS_HEAD + str(screen_id), consist.TITLE_DISK, graph_id))

        exist = sync_redis.smembers(consist.REDIS_HEAD + namespace)
        if not exist:
            sync_redis.sadd(consist.REDIS_HEAD + namespace, screen_id)

    log.info("sync complete")


if __name__ == '__main__':
    r = redis.StrictRedis(host='localhost', port=6379, db=1)
    while True:
        mm_conn = DB(consist.MACHINE_MANAGER_DB_HOST, consist.MACHINE_MANAGER_DB_PORT,
                             consist.MACHINE_MANAGER_DB_USER,
                             consist.MACHINE_MANAGER_DB_PASSWD, consist.MACHINE_MANAGER_DB_NAME)

        db_conn = DB(consist.DASHBOARD_DB_HOST, consist.DASHBOARD_DB_PORT, consist.DASHBOARD_DB_USER,
                               consist.DASHBOARD_DB_PASSWD,
                               consist.DASHBOARD_DB_NAME)

        fp_conn = DB(consist.FALCON_PORTAL_DB_HOST, consist.FALCON_PORTAL_DB_PORT,
                                   consist.FALCON_PORTAL_DB_USER,
                                   consist.FALCON_PORTAL_DB_PASSWD,
                                   consist.FALCON_PORTAL_DB_NAME)

        sync_dashboard(r, mm_conn, db_conn, fp_conn)
        mm_conn._conn.close()
        db_conn._conn.close()
        fp_conn._conn.close()
        time.sleep(600)














