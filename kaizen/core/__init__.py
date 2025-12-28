
class Ether:
    """A medium for communication"""

    def __init__(self, *args, **kwargs):
        pass

    def send(self, msg):
        raise NotImplementedError

    def recv(self, trace, msg_types, sender_set):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

    def post(self, posting):
        raise NotImplementedError

    def register(self, agent):
        raise NotImplementedError

    def unregister(self, agent):
        raise NotImplementedError

    def begin_trace(self, msg):
        raise NotImplementedError

    def end_trace(self, trace):
        raise NotImplementedError

class Channel:
    def __init__(self, name: str):
        self.name = name

    def __str__(self):
        return f"Channel({self.name})"

    __repr__ = __str__

CHANNEL_PROD = Channel("prod")
CHANNEL_DEBUG = Channel("debug")

class Router:
    pass

class Agent:
    def __init__(self, *args, **kwargs):
        pass

    def start(self, ether, channels):
        self.ether = ether
        self.in_channel = channels[0]
        self.out_channel = channels[1]

    def stop(self):
        pass

    def run(self):
        raise NotImpementedError

class WorkflowAgent(Agent):
    def run_interactive(self, *args, **kwargs):
        raise NotImplementedError

class Postings:
    def __init__(self, *args, **kwargs):
        pass

    def post(self):
        pass

class AsyncMessage:
    def __init__(self, channel, type_, sender, contents, sources, trace, *args, **kwargs):
        self.channel = channel
        self.type_ = type_
        self.sender = sender
        self.contents = contents
        self.trace = trace
        self.attachments = []
        self.sources_ = sources if sources is not None else []
        self.message_id = None

        src_trace_ids = set([s.trace_id for s in sources])
        assert len(src_trace_ids) <= 1, f"Cannot have sources from different traces!"

    def attach(self, attachment):
        self.attachments.append(attachment)

    def __str__(self):
        return f"AsyncMessage({self.channel}, {self.trace.trace_id if self.trace else '-'}, {self.message_id}, {str(self.sender)}, {self.type_}, {len(self.contents)})"

    @property
    def sources(self):
        return self.sources_

class SystemMessage(AsyncMessage):
    pass

class SysShutdown(SystemMessage):
    pass

class SysRestart(SystemMessage):
    pass

class Attachment:
    def __init__(self, message, type_, contents, *args, **kwargs):
        self.message = message
        self.type_ = type_
        self.contents = contents

    def __str__(self):
        return f"{self.__class__.__name__}({str(self.message)}, {self.type_}, {len(self.contents)})"

    __repr__ = __str__

    @property
    def data(self):
        return self._data

class Blob(Attachment):
    pass

class ArchiveBlob(Attachment):
    """Archive blob contains a compressed archive that can be used to move
       files and directories around.
    """

    @staticmethod
    def package(self, files):
        pass

    def unpack(self, destination):
        pass

class Trace:
    """A DAG of messages"""

    def __init__(self, name, trace_id, start, duration, active, *args, **kwargs):
        self.name = name
        self.trace_id = trace_id
        self.start = start
        self.duration = duration
        self.expiry = start + duration
        self.active = active

    def __str__(self):
        return f"Trace({self.trace_id}, {self.start}, {self.duration}, {self.active})"

    __repr__ = __str__

