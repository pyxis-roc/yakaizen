#!/usr/bin/env python3

import sys
import datetime

from kaizen.core import WorkflowAgent, AsyncMessage
from kaizen.agent import SimpleWorkflowAgent, agent_main

DUR_5MIN = datetime.timedelta(minutes=5)

AGENT = 'kza-ping'

class PingAgent(SimpleWorkflowAgent):
    name = AGENT
    description = "Ping workflowagent, sends message to be echo'ed"

    def run_interactive(self):
        msg = AsyncMessage(self.out_channel, 'Ping', self,
                           'ping 0', [], None)

        trace = self.ether.begin_trace('ping-pong', msg, DUR_5MIN)
        print('trace begun', trace.trace_id)

        for msg in self.ether.recv(self.in_channel, trace, ('Echo',)):
            print(msg.contents)
            no = int(msg.contents[len('Echo ping '):])
            replymsg = AsyncMessage(self.out_channel, 'Ping', self,
                                    f'ping {no+1}', [], trace)

            self.ether.send(replymsg)

        self.ether.end_trace(trace)

def main():
    agent = PingAgent()
    agent_main(agent, agent.run_interactive)

if __name__ == "__main__":
    main()

