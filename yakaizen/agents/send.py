#!/usr/bin/env python3

import sys
import datetime

from kaizen.core import WorkflowAgent, AsyncMessage
from kaizen.agent import SimpleWorkflowAgent, agent_main

DUR_5MIN = datetime.timedelta(minutes=5)

AGENT = 'kza-send'

class SendAgent(SimpleWorkflowAgent):
    name = AGENT
    description = "Send Workflowagent, sends a particular message"

    def inject_args(self, parser):
        super().inject_args(parser)
        parser.add_argument("message_type", help="Message Type")
        parser.add_argument("message_contents", nargs="?", help="Message Contents")

    def setup(self, args):
        if super().setup(args):
            self.send_message_type = args.message_type
            self.send_message_contents = args.message_contents
            return True
        else:
            return False

    def run_interactive(self):
        msg = AsyncMessage(self.out_channel, self.send_message_type, self,
                           self.send_message_contents, [], None)

        trace = self.ether.begin_trace('send', msg, DUR_5MIN)
        for msg in self.ether.recv(self.in_channel, trace, None):
            print(msg.contents)

        self.ether.end_trace(trace)

def main():
    agent = SendAgent()
    agent_main(agent, agent.run_interactive)

if __name__ == "__main__":
    main()

