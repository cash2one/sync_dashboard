import MySQLdb
import MySQLdb.cursors
from logger import log
import consist
import time


def connect_db(host, port, user, password, db):
    try:
        conn = MySQLdb.connect(
            host=host,
            port=port,
            user=user,
            passwd=password,
            db=db,
            use_unicode=True,
            charset="utf8")
        return conn
    except Exception, e:
        log.error("Fatal: connect db fail:%s" % e)
        return None


class DB(object):

    def __init__(self, host, port, user, password, db):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.db = db
        self._conn = connect_db(host, port, user, password, db)

    def connect(self):
        self._conn = connect_db(self.host, self.port, self.user, self.password, self.db)
        return self._conn

    def execute(self, *a, **kw):
        # type: (object, object) -> object
        cursor = kw.pop('cursor', None)
        try:
            cursor = cursor or self._conn.cursor()
            cursor.execute(*a, **kw)
        except (AttributeError, MySQLdb.OperationalError):
            self._conn and self._conn.close()
            #self.connect()
            self.reconnect()
            cursor = self._conn.cursor()
            cursor.execute(*a, **kw)
        return cursor

    def commit(self):
        if self._conn:
            try:
                self._conn.commit()
            except MySQLdb.OperationalError:
                self._conn and self._conn.close()
                #self.connect()
                self.reconnect()
                self._conn and self._conn.commit()

    def rollback(self):
        if self._conn:
            try:
                self._conn.rollback()
            except MySQLdb.OperationalError:
                self._conn and self._conn.close()
                self.connect()
                self._conn and self._conn.rollback()

    def reconnect(self, number=14400, stime=30):
        num = 0
        status = True
        while num <= number and status:
            self.connect()
            if self._conn:
                status = False
                break
            num += 1
            time.sleep(stime)


machine_db_conn = DB(consist.MACHINE_MANAGER_DB_HOST, consist.MACHINE_MANAGER_DB_PORT, consist.MACHINE_MANAGER_DB_USER,
                     consist.MACHINE_MANAGER_DB_PASSWD, consist.MACHINE_MANAGER_DB_NAME)

dashboard_db_conn = DB(consist.DASHBOARD_DB_HOST, consist.DASHBOARD_DB_PORT, consist.DASHBOARD_DB_USER,
                       consist.DASHBOARD_DB_PASSWD,
                       consist.DASHBOARD_DB_NAME)

falcon_portal_db_conn = DB(consist.FALCON_PORTAL_DB_HOST, consist.FALCON_PORTAL_DB_PORT, consist.FALCON_PORTAL_DB_USER,
                           consist.FALCON_PORTAL_DB_PASSWD,
                           consist.FALCON_PORTAL_DB_NAME)