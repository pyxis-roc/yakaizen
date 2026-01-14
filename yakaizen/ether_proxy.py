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
        if cmd.cmd == 'recv':
            p = _decode(cmd.payload)
            rv = list(self.ethsq.recv(*p['args'], **p['kwargs'], blocking=False))
            return CMD('ret', rv)
        elif cmd.cmd == 'send':
            p = _decode(cmd.payload)
            self.ethsq.send(*p['args'], **p['kwargs'])
            return CMD('ret', p['args'][0].message_id)
        elif cmd.cmd == 'begin_trace':
            p = _decode(cmd.payload)
            msg = p['args'][1]
            ret = self.ethsq.begin_trace(*p['args'], **p['kwargs'])
            return CMD('ret', (ret, msg.message_id))
        elif cmd.cmd == 'end_trace':
            p = _decode(cmd.payload)
            self.ethsq.end_trace(*p['args'], **p['kwargs'])
            return CMD('ret', None)
        else:
            print("Unhandled ", cmd.cmd)
            return CMD('ret', None)

    def run_proxy(self):
        with pynng.Rep0(listen=self.listen_addr) as rep:
            try:
                while True:
                    pcmd = rep.recv()
                    cmd = pickle.loads(pcmd)
                    if isinstance(cmd, CMD):
                        ret = self._dispatch(cmd)
                        assert ret is not None
                        rep.send(pickle.dumps(ret))
                    else:
                        print(f"ERROR: received {type(cmd)}, expected {type(CMD)}")
            except KeyboardInterrupt:
                print("Received CTRL+C, shutting down proxy")



def check_ret(ret, src):
    if not isinstance(ret, CMD) or ret.cmd != 'ret':
        print(f"ERROR: received malformed return value for {src}", ret)
        return False

    return True

class ProxyEther(Ether):
    def __init__(self, dial_addr, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proxy = pynng.Req0(dial=dial_addr)

    def send(self, msg):
        self.proxy.send(_encode('send', msg))
        ret = pickle.loads(self.proxy.recv())

        msg.message_id = ret.payload

    def begin_trace(self, name, msg, duration):
        self.proxy.send(_encode('begin_trace', name, msg, duration))
        ret = pickle.loads(self.proxy.recv())

        if not check_ret(ret, 'begin_trace'):
            return None

        msg.message_id = ret.payload[1]
        return ret.payload[0]

    def end_trace(self, trace):
        self.proxy.send(_encode('end_trace', trace))
        ret = pickle.loads(self.proxy.recv())
        if not check_ret(ret, 'end_trace'):
            return None

        trace.active = False

    def recv(self, channel, trace, msg_types, sender_set = None, blocking = True):
        start = datetime.datetime.utcnow()
        try:
            while True:
                self.proxy.send(_encode('recv', channel, trace,
                                        msg_types, sender_set=sender_set,
                                        _start = start))

                ret = pickle.loads(self.proxy.recv())
                if not check_ret(ret, 'recv'):
                    continue # ignore malformed messages

                for r in ret.payload:
                    yield r

                if len(ret.payload):
                    start = ret.payload[-1]._sent

                if blocking:
                    time.sleep(1) # TODO: need to turn this into a notification instead of polling.
                else:
                    break
        except KeyboardInterrupt:
            print("Detected CTRL+C, shutting down recv loop")

ProxyableEthers = {'sqlite': SQLiteProxyEther}

def main():
    import argparse

    p = argparse.ArgumentParser(description='Start a Kaizen proxy server')
    p.add_argument('--kz-ether', help='Proxy to this ether', choices=ProxyableEthers.keys())
    p.add_argument('--kz-ether-args', help='Arguments for ether')
    p.add_argument('listen_addr', nargs='?', default='tcp://127.0.0.1:43789/')

    args = p.parse_args()

    if args.kz_ether is None:
        print("ERROR: --kz_ether required")
        sys.exit(1)

    if args.kz_ether is None:
        print("ERROR: Sqlite ether requires database as argument")
        sys.exit(1)


    listen_addr = args.listen_addr
    db = args.kz_ether_args

    print(f"Listening on {args.listen_addr} and proxying to {args.kz_ether}/{args.kz_ether_args}")
    print("Use CTRL+C or CTRL+\ to quit")
    srv = ProxyableEthers[args.kz_ether](listen_addr, db)
    srv.run_proxy()

if __name__ == "__main__":
    main()
