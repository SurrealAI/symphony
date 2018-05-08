import zmq


class ZmqError(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message


class ZmqTimeoutError(Exception):
    def __init__(self):
        super().__init__('Request Timed Out')


class ZmqSocketWrapper(object):
    """
        Wrapper around zmq socket, manages resources automatically
    """
    def __init__(self, mode, bind, address=None, host=None, port=None, context=None, silent=False):
        """
        Args:
            @host: specifies address, localhost is translated to 127.0.0.1
            @address
            @port: specifies address
            @mode: zmq.PUSH, zmq.PULL, etc.
            @bind: True -> bind to address, False -> connect to address (see zmq)
            @context: Zmq.Context object, if None, client creates its own context
            @silent: set to True to prevent printing
        """
        if address is not None:
            self.address = address
        else:
            # https://stackoverflow.com/questions/6024003/why-doesnt-zeromq-work-on-localhost
            assert host is not None and port is not None
            # Jim's note, ZMQ does not like localhost
            if host == 'localhost':
                host = '127.0.0.1'
            self.address = "tcp://{}:{}".format(host, port)

        if context is None:
            self.context = zmq.Context()
            self.owns_context = True
        else:
            self.context = context
            self.owns_context = False

        self.mode = mode
        self.bind = bind
        self.socket = self.context.socket(self.mode)
        self.established = False
        self.silent = silent

    def establish(self):
        """
            We want to allow subclasses to configure the socket before connecting
        """
        if self.established:
            raise RuntimeError('Trying to establish a socket twice')
        self.established = True
        if self.bind:
            if not self.silent:
                print('[{}] binding to {}'.format(self.socket_type, self.address))
            self.socket.bind(self.address)
        else:
            if not self.silent:
                print('[{}] connecting to {}'.format(self.socket_type, self.address))
            self.socket.connect(self.address)
        return self.socket

    def __del__(self):
        if self.established:
            self.socket.close()
        if self.owns_context: # only terminate context when we created it
            self.context.term()

    @property
    def socket_type(self):
        if self.mode == zmq.PULL:
            return 'PULL'
        elif self.mode == zmq.PUSH:
            return 'PUSH'
        elif self.mode == zmq.PUB:
            return 'PUB'
        elif self.mode == zmq.SUB:
            return 'SUB'
        elif self.mode == zmq.PAIR:
            return 'PAIR'
        elif self.mode == zmq.REQ:
            return 'REQ'
        elif self.mode == zmq.REP:
            return 'REP'
        elif self.mode == zmq.ROUTER:
            return 'ROUTER'
        elif self.mode == zmq.DEALER:
            return 'DEALER'

##
# Sender receiver implemented by REQ-REP
##
class ZmqSender(ZmqSocketWrapper):
    def __init__(self, host, port, preprocess=None):
        super().__init__(host=host, port=port, mode=zmq.REQ, bind=False)
        self.preprocess = preprocess
        self.establish()

    def send(self, data):
        if self.preprocess:
            data = self.preprocess(data)
        self.socket.send(data)
        resp = self.socket.recv()
        return resp


class ZmqReceiver(ZmqSocketWrapper):
    def __init__(self, host, port, bind=True, preprocess=None):
        super().__init__(host=host, port=port, mode=zmq.REP, bind=bind)
        self.preprocess = preprocess
        self.establish()

    def recv(self):
        data = self.socket.recv()
        if self.preprocess:
            data = self.preprocess(data)
        self.socket.send(b'ack') # doesn't matter
        return data
