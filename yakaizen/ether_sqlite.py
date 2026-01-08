from .core import Ether, Trace, AsyncMessage
import sqlite3
import datetime
import time

def s2dt(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")

class SQLiteEther(Ether):
    """A ether running on top of a SQLite database"""

    def __init__(self, database, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = database
        self._setup_database()

    def _setup_database(self):
        setup_sql = """
CREATE TABLE IF NOT EXISTS channels (id INTEGER PRIMARY KEY, name TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS traces (id INTEGER PRIMARY KEY, start DATETIME NOT NULL, expiry DATETIME, active BOOLEAN, name TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, channel TEXT NOT NULL, type TEXT NOT NULL, sender TEXT NOT NULL, contents TEXT, has_attachments BOOLEAN, sent DATETIME NOT NULL, trace_id INTEGER NOT NULL, starts_trace BOOLEAN NOT NULL, FOREIGN KEY(trace_id) REFERENCES traces(id));

CREATE INDEX IF NOT EXISTS messages_sent ON messages(sent);

CREATE TABLE IF NOT EXISTS message_sources (msg_id INTEGER, src_msg_id INTEGER, FOREIGN KEY(msg_id) REFERENCES messages(id), FOREIGN KEY(src_msg_id) REFERENCES messages(id));

CREATE TABLE IF NOT EXISTS attachments (id INTEGER PRIMARY KEY, message_id INTEGER, type TEXT NOT NULL, contents BLOB, FOREIGN KEY(message_id) REFERENCES messages(id));

CREATE TABLE IF NOT EXISTS postings (id INTEGER PRIMARY KEY, name TEXT UNIQUE, type TEXT, contents BLOB);
"""
        with self._get_conn() as conn:
            conn.executescript(setup_sql)
            conn.commit()

    def _get_conn(self):
        conn = sqlite3.connect(self.database, autocommit=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _send(self, conn, msg):
        assert msg.type_ is not None
        assert msg.sender is not None
        assert msg.trace is not None

        if len(msg.sources) > 0:
            raise NotImplementedError

        if len(msg.attachments) > 0:
            raise NotImplementedError

        cur = conn.cursor()
        cur.execute('INSERT INTO messages (channel, type, sender, contents, has_attachments, sent, trace_id, starts_trace) VALUES (?,?,?,?,?,?,?,?)',
                    (msg.channel.name, msg.type_, msg.sender, msg.contents,
                     len(msg.attachments) > 0,
                     datetime.datetime.utcnow(),
                     msg.trace.trace_id, False))

        msg.message_id = cur.lastrowid
        cur.close()

    def send(self, msg):
        assert msg.message_id is None, f"Can't resend message"
        assert msg.trace is not None, f"Use begin_trace to send a message that starts a trace"

        with self._get_conn() as conn:
            self._send(conn, msg)
            conn.commit()

    def begin_trace(self, name, msg, duration):
        assert msg.trace is None

        start = datetime.datetime.utcnow()
        expiry = start + duration

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO traces (name, start, expiry, active) VALUES (?,?,?,?)',
                        (name, start, expiry, True))

            trace_id = cur.lastrowid
            cur.close()

            msg.trace = Trace(name, trace_id, start, duration, True)
            self._send(conn, msg)

            conn.commit()

            return msg.trace

    def end_trace(self, trace):
        assert trace.trace_id is not None
        assert trace.active

        with self._get_conn() as conn:
            cur = conn.cursor()
            cur.execute('UPDATE traces SET active=FALSE WHERE id = ?', (trace.trace_id,))
            cur.close()
            conn.commit()

        trace.active = False

    # TODO: recv header to only get headers of messages retrieving bodies and attachments later
    # TODO: support NOT IN
    def recv(self, channel, trace, msg_types, sender_set = None, blocking = True, _start = None):
        traces_cache = {}

        def build_in_set(x):
            return "(" + ','.join(["'" + xx + "'" for xx in x]) + ")"

        def get_trace(conn, trace_id):
            if trace_id not in traces_cache:
                cur = conn.cursor()
                res = cur.execute('SELECT * FROM traces WHERE id = ?', (trace_id,))
                row = cur.fetchone()
                assert row is not None
                cur.close()

                start = s2dt(row['start'])
                expiry = s2dt(row['expiry'])

                trace = Trace(row['id'], start, expiry - start, row['active'])
                traces_cache[trace_id] = trace

            return traces_cache[trace_id]

        def get_trace_2(row):
            trace_id = row['trace_id']
            if trace_id not in traces_cache:
                start = s2dt(row['start'])
                expiry = s2dt(row['expiry'])

                trace = Trace(row['name'], row['trace_id'], start, expiry - start, row['active'])
                traces_cache[trace_id] = trace

            return traces_cache[trace_id]

        def convert(conn, row):
            trace = get_trace_2(row)
            msg = AsyncMessage(row['channel'], row['type'], row['sender'],
                               row['contents'], [], trace)
            msg._sent = row['sent']
            msg.message_id = row['id']

            return msg

        values = {'channel': channel.name}

        constraints = []

        if trace is not None:
            assert trace.trace_id is not None
            values['trace'] = trace.trace_id
            constraints.append('trace_id = :trace')

        if msg_types is not None:
            values['msg_types'] = msg_types
            constraints.append(f'type IN {build_in_set(msg_types)}')

        if sender_set is not None:
            values['sender_set'] = sender_set
            constraints.append(f'sender IN {build_in_set(sender_set)}')

        query = 'SELECT * FROM messages, traces WHERE messages.trace_id = traces.id AND traces.active = TRUE AND messages.sent > :start AND ' + ' AND '.join(constraints) + ' ORDER BY messages.sent;'
        cur = None

        #TODO: possibly make this the oldest active trace?
        values['start'] = _start or datetime.datetime.utcnow()
        try:
            while True:
                rows = []
                with self._get_conn() as conn:
                    cur = conn.cursor()
                    res = cur.execute(query, values)
                    rows = list([convert(conn, row) for row in res.fetchall()])
                    cur.close()

                if len(rows) > 0:
                    for msg in rows:
                        yield msg

                    # race conditions here ...
                    values['start'] = rows[-1]._sent

                if blocking:
                    time.sleep(1) # TODO: need to turn this into a notification instead of polling.
                else:
                    break
        except KeyboardInterrupt:
            print("Detected CTRL+C, shutting down recv loop")


