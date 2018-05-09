import msgpack

import asyncio
import uuid


class MsgpackProtocol (asyncio.Protocol):

    def __init__(self, delegate, pid=None):
        self.pid = pid or str(uuid.uuid4())
        self.delegate = delegate
        self.unpacker = msgpack.Unpacker(use_list=False, raw=False)
        self.transport = None
        self.address = ''
        self.port = 0

    def connection_made(self, transport):
        self.transport = transport
        self.address, self.port = transport.get_extra_info('peername')
        self.delegate.connected(self)

    def data_received(self, data):
        self.unpacker.feed(data)
        for (cmd, args) in self.unpacker:
            self.delegate.handle(self, cmd, **args)

    def connection_lost(self, exc):
        self.delegate.disconnected(self)

    def send(self, cmd, **args):
        data = msgpack.packb((cmd, args), use_bin_type=True)
        self.transport.write(data)
