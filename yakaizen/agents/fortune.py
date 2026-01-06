import sys

from yakaizen.core import Agent, AsyncMessage
from yakaizen.agent import SimpleAgent, agent_main
from yakaizen.utils.runner import run

AGENT = 'kza-fortune'

class FortuneAgent(SimpleAgent):
    name = AGENT
    description = "Fortune Agent, runs the `fortune` command and returns its output."

    def get_recv_args(self):
        return (self.in_channel, # channel
                None, # trace, None means all active traces
                ('Ask-Fortune',) # tuple of message types
        )

    def handle_message(self, msg):
        rr = run(['fortune'])
        if rr.success:
            message = rr.output
        else:
            if rr.exception:
                message = f'Failed with {rr.exception}'
            else:
                message = f'Fortune failed with {rr.errors}'

        reply = AsyncMessage(self.out_channel, 'Fortune', self, message, [], msg.trace)
        return reply

def main():
    agent = FortuneAgent()
    agent_main(agent, agent.run)

if __name__ == "__main__":
    main()
