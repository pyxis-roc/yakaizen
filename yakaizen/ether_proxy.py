import sqlite3
import datetime
import time
import pynng
from collections import namedtuple
import pickle

from .core import Ether, Trace, AsyncMessage
from .ether_sqlite import SQLiteEther

CMD = namedtuple('CMD', 'cmd payload')

def _encode(cmd, *args, **kwargs):
    payload = pickle.dumps({'args': args, 'kwargs': kwargs})
    return pickle.dumps(CMD(cmd, payload))

def _decode(payload):
    return pickle.loads(payload)

class SQLiteProxyEther(Ether):
    def __init__(self, listen_addr, database, *args, **kwargs):
        self.ethsq = SQLiteEther(database, *args, **kwargs)
        self.listen_addr = listen_addr

    def _dispatch(self, cmd):
        print('dispatch', cmd.cmd)
        if cmd.cmd == 'recv':
            p = _decode(cmd.payload)
            rv = list(self.ethsq.recv(*p['args'], **p['kwargs'], blocking=False))
            if len(rv): print(len(rv))
            return CMD('ret', rv)
        elif cmd.cmd == 'send':
            p = _decode(cmd.payload)
            self.ethsq.send(*p['args'], **p['kwargs'])
            return CMD('ret', p['args'][0].message_id)
        elif cmd.cmd == 'begin_trace':
            p = _decode(cmd.payload)
            ret = self.ethsq.begin_trace(*p['args'], **p['kwargs'])
            print("ret value for begin_trace", ret)
            return CMD('ret', ret)
        else:
            print("Unhandled ", cmd.cmd)
            return CMD('ret', None)

    def run_proxy(self):
        with pynng.Rep0(listen=self.listen_addr) as rep:
            while True:
                pcmd = rep.recv()
                cmd = pickle.loads(pcmd)
                if isinstance(cmd, CMD):
                    ret = self._dispatch(cmd)
                    assert ret is not None
                    rep.send(pickle.dumps(ret))
                else:
                    print(f"ERROR: received {type(cmd)}, expected {type(CMD)}")

class ProxyEther(Ether):
    def __init__(self, dial_addr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy = pynng.Req0(dial=dial_addr)

    def send(self, msg):
        print('sending', msg)
        self.proxy.send(_encode('send', msg))
        ret = pickle.loads(self.proxy.recv())
        if not isinstance(ret, CMD) and ret.cmd != 'ret':
            print(f"ERROR: received malformed return value for send", ret)
            return None

        msg.message_id = ret.payload

    def begin_trace(self, name, msg, duration):
        self.proxy.send(_encode('begin_trace', name, msg, duration))
        ret = pickle.loads(self.proxy.recv())
        if not isinstance(ret, CMD) and ret.cmd != 'ret':
            print(f"ERROR: received malformed return value for begin_trace", ret)
            return None
        return ret.payload

    def end_trace(self, trace):
        print('ending trace')
        self.proxy.send(_encode('end_trace', trace))
        ret = self.proxy.recv()

    def recv(self, channel, trace, msg_types, sender_set = None, blocking = True):
        start = datetime.datetime.utcnow()
        while True:
            self.proxy.send(_encode('recv', channel, trace,
                                    msg_types, sender_set=sender_set,
                                    _start = start))

            ret = pickle.loads(self.proxy.recv())
            if not isinstance(ret, CMD) and ret.cmd != 'ret':
                print(f"ERROR: received malformed return value for recv", ret)
                continue

            for r in ret.payload:
                yield r

            if len(ret.payload):
                start = ret.payload[-1]._sent

            if blocking:
                time.sleep(1) # TODO: need to turn this into a notification instead of polling.
            else:
                break

def main():
    listen_addr = 'tcp://127.0.0.1:9999'
    db = 'test.db'

    srv = SQLiteProxyEther(listen_addr, db)
    srv.run_proxy()

if __name__ == "__main__":
    main()
