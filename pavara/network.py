from panda3d.core import LVecBase3f, LVecBase4f
import msgpack

import asyncio
import socket
import uuid


def _pack_vec(obj):
    if isinstance(obj, LVecBase3f):
        return {'__type__': 'LVecBase3f', 'xyz': (obj.x, obj.y, obj.z)}
    elif isinstance(obj, LVecBase4f):
        return {'__type__': 'LVecBase4f', 'xyzw': (obj.x, obj.y, obj.z, obj.w)}
    return obj


def _unpack_vec(obj):
    if obj.get('__type__') == 'LVecBase3f':
        return LVecBase3f(*obj['xyz'])
    elif obj.get('__type__') == 'LVecBase4f':
        return LVecBase4f(*obj['xyzw'])
    return obj


class MsgpackProtocol (asyncio.Protocol):

    def __init__(self, delegate, pid=None):
        self.pid = pid or str(uuid.uuid4())
        self.delegate = delegate
        self.unpacker = msgpack.Unpacker(use_list=False, raw=False, object_hook=_unpack_vec)
        self.transport = None
        self.address = ''
        self.port = 0

    def connection_made(self, transport):
        transport.get_extra_info('socket').setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
        data = msgpack.packb((cmd, args), use_bin_type=True, default=_pack_vec)
        self.transport.write(data)
