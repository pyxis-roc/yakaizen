import sys

from kaizen.core import Agent, AsyncMessage
from kaizen.agent import SimpleAgent, agent_main

AGENT = 'kza-echo'

class EchoAgent(SimpleAgent):
    name = AGENT
    description = "Echo Agent, just echoes the contents of each message."

    def get_recv_args(self):
        return (self.in_channel, # channel
                None, # trace, None means all active traces
                ('Ping',) # tuple of message types
        )

    def handle_message(self, message):
        return AsyncMessage(self.out_channel, 'Echo', self, 'Echo ' + message.contents,
                            [], message.trace)

def main():
    agent = EchoAgent()
    agent_main(agent, agent.run)

if __name__ == "__main__":
    main()
