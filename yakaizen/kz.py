import argparse
import sys
from pathlib import Path
import configparser
import shutil
import shlex
import subprocess

def start_agent(agent, config, args):
    print(f"Starting {agent}")

    # initial version, assume agent is a direct command
    cmd = shutil.which(agent)
    if cmd is None:
        print(f"ERROR: Agent {agent} is not a runnable command.")
        return False

    # construct standard command line
    ether = config['workflow-config']['ether']
    kz_ether_arg = args.kz_ether_arg

    cmdline = [cmd, '--kz-ether', ether]
    if kz_ether_arg is not None:
        cmdline.extend(['--kz-ether-arg', kz_ether_arg])

    try:
        p = subprocess.Popen(cmdline, close_fds = True)
        return p
    except OSError as e:
        print(e, file=sys.stderr)
        return None

    return None

def do_run_agent(args):
    cfg = load_config(args.config)

    is_all = any([x == 'all' for x in args.agent])

    if is_all and len(args.agent) != 1:
        print("'all' cannot be mixed with other agents")
        sys.exit(1)

    try:
        name = cfg.get('workflow-config', 'name')
        ether = cfg.get('workflow-config', 'ether')
        agents = cfg.get('workflow-config', 'agents')
        agents = set(agents.split(":"))
    except KeyError as e:
        print(e)
        print(f"ERROR: Invalid configuration file")
        sys.exit(1)

    if len(agents) == 0:
        print(f"ERROR: No agents in config")
        sys.exit(1)

    if not is_all:
        for a in args.agent:
            if a not in agents:
                print(f"ERROR: {args.agent} not found in config: agents={':'.join(agents)}")
                sys.exit(1)

        agents = agents.intersection(set(args.agents))

    processes = []
    for a in agents:
        p = start_agent(a, cfg, args)
        if not p:
            print(f"ERROR: Failed to start agent {a}. Terminating other agents started.")
            for (ag, other_p) in processes:
                print(f"Terminating {ag}")
                other_p.terminate()

            return
        else:
            processes.append((a, p))

    for a, p in processes:
        try:
            p.wait()
            print(a, "terminated")
        except KeyboardInterrupt:
            pass

def load_config(config):
    if not config.exists():
        print(f"ERROR: {config} does not exist")
        sys.exit(1)

    cfg = configparser.ConfigParser()
    cfg.read(config)
    return cfg

def do_create_config(args):
    if args.config.exists():
        print(f"ERROR: {args.config} already exists.")
        sys.exit(1)

    cfg = configparser.ConfigParser()
    cfg['main'] = {'version': '1',
                   'type': 'kz-workflow'}
    cfg['workflow-config'] = {'name': args.workflow_name,
                              'ether': args.ether,
                              'workflow_agent': args.workflow_agent,
                              'agents': ":".join(args.agent)}

    cfg[f'ether:{args.ether}'] = {}

    with open(args.config, "w") as f:
        cfg.write(f)

def main():
    p = argparse.ArgumentParser(description="Run Kaizen workflows")

    p.add_argument("config", help="Config file", type=Path)

    sp = p.add_subparsers(dest='cmd')

    cc = sp.add_parser('create-config', help="Create a configuration file")

    cc.add_argument("workflow_name", help="Workflow name")
    cc.add_argument("ether", help="Ether provider", choices=['sqlite'])
    cc.add_argument("workflow_agent", help="Workflow agent")
    cc.add_argument("--agent", action="append", help="Agent to include in workflow", default=[])

    ra = sp.add_parser('run-agent', help="Run an agent")
    ra.add_argument("agent", nargs="+", help="Agents to run, 'all' for all agents in config")
    ra.add_argument("--kz-ether-arg", help="--kz-ether-arg to pass to agent")

    rw = sp.add_parser('run-workflow', help="Run the workflow agent from a config")
    rw.add_argument("args", nargs='+', help='Arguments to pass to workflow agent')

    args = p.parse_args()

    if args.cmd == "create-config":
        do_create_config(args)
    elif args.cmd == "run-agent":
        do_run_agent(args)
    else:
        print(f"ERROR: Not implemented {args.cmd}")

if __name__ == "__main__":
    main()
