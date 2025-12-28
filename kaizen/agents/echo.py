import sys

from kaizen.core import Agent, AsyncMessage
from kaizen.agent import SimpleAgent, agent_main

AGENT = 'kza-echo'

class EchoAgent(SimpleAgent):
    name = AGENT
    description = "Echo Agent, just echoes the contents of each message."

    def run(self):
        for msg in self.ether.recv(self.in_channel, None, ('Ping',)):
            reply = AsyncMessage(self.out_channel, 'Echo', self, 'Echo ' + msg.contents, [], msg.trace)
            self.ether.send(reply)

def main():
    agent = EchoAgent()
    agent_main(agent, agent.run)

if __name__ == "__main__":
    main()
