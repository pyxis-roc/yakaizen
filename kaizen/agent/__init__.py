import sys
import kaizen.ether_sqlite as ethsqlite
from kaizen.core import CHANNEL_PROD, CHANNEL_DEBUG, Channel

class AgentHelper:
    def __init__(self):
        pass

    @staticmethod
    def inject_kz_args(args):
        args.add_argument("--kz-ether", help="Kaizen Ether specification")
        args.add_argument("--kz-ether-args", help="Kaizen ether arguments")
        args.add_argument("--kz-cin", help="Kaizen input channel")
        args.add_argument("--kz-cout", help="Kaizen output channel, should not used except in special circumstances")

    @staticmethod
    def get_ether(agent, args):
        if args.kz_ether is None:
            print(f"{agent}:ERROR: No ether specified.", file=sys.stderr)
            return None

        if args.kz_ether != 'sqlite':
            print(f"{agent}:ERROR: ether {args.kz_ether} is not recognized.", file=sys.stderr)
            return None

        if args.kz_ether == 'sqlite':
            if args.kz_ether_args is None:
                print(f"{agent}:ERROR: ether sqlite requires a database file as argument.", file=sys.stderr)
                return None

            return ethsqlite.SQLiteEther(args.kz_ether_args)

    @staticmethod
    def get_channels(agent, ether, args):
        cin = Channel(args.kz_cin) if args.kz_cin else CHANNEL_PROD
        cout = Channel(args.kz_cout) if args.kz_cout else cin

        return (cin, cout)

    @staticmethod
    def init_message(agent, ether, channels):
        print(f"SUCCESS: Agent {agent} started, listening to in={channels[0]}, out={channels[0]}", file=sys.stderr)

