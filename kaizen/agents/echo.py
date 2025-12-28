import sys

from kaizen.core import Agent, AsyncMessage
from kaizen.agent import AgentHelper as AH

AGENT = 'kza-echo'

class EchoAgent(Agent):
    name = AGENT

    def run(self):
        for msg in self.ether.recv(self.in_channel, None, ('Ping',)):
            print(msg)
            reply = AsyncMessage(self.out_channel, 'Echo', self, msg.contents, [], msg.trace)
            self.ether.send(reply)

def main():
    import argparse

    p = argparse.ArgumentParser(description="Echo Agent, just echoes the contents of each message")

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
    agent = EchoAgent()
    agent.start(ether, channels)
    agent.run()

if __name__ == "__main__":
    main()
