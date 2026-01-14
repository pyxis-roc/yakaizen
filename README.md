# yakaizen

Yet Another Kaizen is a framework for creating asynchronous workflows
with message-passing "agents."

The programming model consists of two kinds of interacting entities:
agents, and workflow-agents.

An agent responds to messages of a particular form -- there is no
point-to-point messaging. All messages are broadcast messages, similar
to a tuplespace.

A workflow agent carries out tasks. It initiates _traces_, which are
messages that are logically part of the same task, represented as a
DAG. A trace can be closed by the workflow agent at any time, but
traces also have a finite lifetime after which they expire. Agents
usually only respond to messages that are part of a unexpired trace.

The framework does guarantee reliable and ordered delivery of messages
to make some aspects of asynchronous programming easier. It also
persists every message.


## Installation

This package is being developed and changes frequently. Clone it, and install as follows:


```
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Demonstration

There is a simple ping-pong message passing example. After installation, switch to the `pingpong` directory:

```
cd pingpong
kz pingpong.cfg run-agent all --kz-ether-arg pingpong.db
```

You should see:

```
Starting kza-echo
SUCCESS: Agent kza-echo started, listening to in=Channel(prod), out=Channel(prod)
```

This starts all the agents required for the workflow. You can use
CTRL+C to stop them. This workflow uses only the `kza-echo` agent.

In another window, you can start the workflow agent as follows:

```
python3 ./ping.py --kz-ether sqlite --kz-ether-args pingpong.db 

```

You should see:

```
SUCCESS: Agent kza-ping started, listening to in=Channel(prod), out=Channel(prod)
trace begun 1
Echo ping 0
Echo ping 1
Echo ping 2
...
```

which will continue until you press CTRL+C (trace expiration isn't implemented yet.)

## Fortune

The `kz` command is for convenience. You can also run agents
directly. Here is an example:

```
kza-fortune --kz-ether sqlite --kz-ether-args test.db
SUCCESS: Agent kza-fortune started, listening to in=Channel(prod), out=Channel(prod)
```

Then, from another window you can send it a message:

```
kza-send --kz-ether sqlite --kz-ether-args test.db Ask-Fortune
```

If the `fortune` command is installed, you should see a fortune:

```
SUCCESS: Agent kza-send started, listening to in=Channel(prod), out=Channel(prod)
It's all in the mind, ya know.
```

Otherwise you will see this error:

```
SUCCESS: Agent kza-send started, listening to in=Channel(prod), out=Channel(prod)
Failed with [Errno 2] No such file or directory: 'fortune'
```

Note `kza-send` and `kza-fortune` need to be shutdown using CTRL+C.


# Proxy-ing Agent Communication

Yakaizen supports running agents on different computers when using the
`sqlite` ether. On the machine where the database is stored, run the
`kz-proxy` command. This is the proxy server.

On the remote machine, start the agent using the `proxy`
ether. Specify the server's listening address as the ether's
arguments.

The `proxy` ether uses `nng` under the hood. This is very reliable and
will resend messages if the connection is broken. This may cause
duplicate messages.

## Using SSH for secure connections.

By default, the `kz-proxy` listens on a localhost address. You can use
SSH to proxy the remote agent's request securely over the network.

On the server, assuming you're using the default server listening address:

```
kz-proxy ...
ssh -R 43789:127.0.0.1:43789 -N user@host
```

Then on `host`, run the agent and provide `tcp://127.0.0.1:43789` as
usual. The communication will now happen securely over the SSH connection.


## Roadmap

- Trace expiration
- Implement attachments to messages
- Implement an interactive trace viewer for debugging
- Implement message aggregators

