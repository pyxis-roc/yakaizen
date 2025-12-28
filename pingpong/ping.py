#!/usr/bin/env python3

import sys
import datetime

from kaizen.core import WorkflowAgent, AsyncMessage
from kaizen.agent import AgentHelper as AH

DUR_5MIN = datetime.timedelta(minutes=5)

AGENT = 'kza-ping'

class PingAgent(WorkflowAgent):
    name = AGENT

    def run_interactive(self):
        msg = AsyncMessage(self.out_channel, 'Ping', self,
                           'ping 0', [], None)

        trace = self.ether.begin_trace('ping-pong', msg, DUR_5MIN)
        print('trace begun', trace.trace_id)

        for msg in self.ether.recv(self.in_channel, trace, ('Echo',)):
            print(msg.contents)
            no = int(msg.contents[len('ping '):])
            replymsg = AsyncMessage(self.out_channel, 'Ping', self,
                                    f'ping {no+1}', [], trace)

            self.ether.send(replymsg)

        self.ether.end_trace(trace)

def main():
    import argparse

    p = argparse.ArgumentParser(description="Ping WorkflowAgent, sends message to be echo'ed")
    AH.inject_kz_args(p)

    args = p.parse_args()

    ether = AH.get_ether(AGENT, args)
    if ether is None:
        sys.exit(1)

    channels = AH.get_channels(AGENT, ether, args)
    if channels is None:
        print("channel setup failed.")
        sys.exit(1)

    AH.init_message(AGENT, ether, channels)

    agent = PingAgent()
    agent.start(ether, channels)
    agent.run_interactive()

if __name__ == "__main__":
    main()

