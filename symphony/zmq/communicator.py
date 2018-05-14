import queue
import zmq
from threading import Thread, Lock
import nanolog as nl
from symphony.utils.threads import start_thread


zmq_log = nl.Logger.create_logger(
    'zmq',
    stream='stdout',
    time_format='hms',
    show_level=True,
)

class ZmqError(Exception):
    def __init__(self, message):
        self.message = message


class ZmqTimeoutError(Exception):
    def __init__(self):
        super().__init__('Request Timed Out')


def str2bytes(string):
    if isinstance(string, bytes):
        return string
    else:
        return string.encode('UTF-8')


class ZmqSocket(object):
    """
        Wrapper around zmq socket, manages resources automatically
    """
    SOCKET_TYPES = {
        'PULL': zmq.PULL,
        'PUSH': zmq.PUSH,
        'PUB': zmq.PUB,
        'SUB': zmq.SUB,
        'REQ': zmq.REQ,
        'REP': zmq.REP,
        'ROUTER': zmq.ROUTER,
        'DEALER': zmq.DEALER,
        'PAIR': zmq.PAIR,
    }

    def __init__(self, mode,
                 bind,
                 address=None,
                 host=None,
                 port=None,
                 context=None,
                 verbose=True):
        """
        Args:
            host: specifies address, localhost is translated to 127.0.0.1
            address
            port: specifies address
            mode: zmq.PUSH, zmq.PULL, etc., or their string names
            bind: True -> bind to address, False -> connect to address (see zmq)
            context: Zmq.Context object, if None, client creates its own context
            verbose: set to True to print log messages
        """
        if address is not None:
            self.address = address
        else:
            # https://stackoverflow.com/questions/6024003/why-doesnt-zeromq-work-on-localhost
            assert host is not None and port is not None
            if host == 'localhost':
                host = '127.0.0.1'
            self.address = "tcp://{}:{}".format(host, port)

        if context is None:
            self._context = zmq.Context()
            self._owns_context = True
        else:
            self._context = context
            self._owns_context = False

        if isinstance(mode, str):
            mode = self.SOCKET_TYPES[mode.upper()]
        self.mode = mode
        self.bind = bind
        self.established = False
        self._socket = self._context.socket(self.mode)
        self._verbose = verbose

    def unwrap(self):
        """
        Get the raw underlying ZMQ socket
        """
        return self._socket

    def establish(self):
        """
            We want to allow subclasses to configure the socket before connecting
        """
        if self.established:
            raise RuntimeError('Trying to establish a socket twice')
        self.established = True
        if self.bind:
            if self._verbose:
                zmq_log.infofmt('[{}] binding to {}', self.socket_type, self.address)
            self._socket.bind(self.address)
        else:
            if self._verbose:
                zmq_log.infofmt('[{}] connecting to {}', self.socket_type, self.address)
            self._socket.connect(self.address)
        return self

    def __getattr__(self, attrname):
        """
        Delegate any unknown methods to the underlying self.socket
        """
        if attrname in dir(self):
            return object.__getattribute__(self, attrname)
        else:
            return getattr(self._socket, attrname)

    def __del__(self):
        if self.established:
            self._socket.close()
        if self._owns_context: # only terminate context when we created it
            self._context.term()

    @property
    def socket_type(self):
        reverse_map = {value: name for name, value in self.SOCKET_TYPES.items()}
        return reverse_map[self.mode]


class ZmqPusher:
    def __init__(self, host, port, serializer=None, hwm=42):
        self.socket = ZmqSocket(host=host, port=port, mode=zmq.PUSH, bind=False)
        self.socket.set_hwm(hwm)
        self.serializer = serializer
        self.socket.establish()

    def push(self, data):
        if self.serializer:
            data = self.serializer(data)
        self.socket.send(data)


class ZmqPuller:
    def __init__(self, host, port, bind, serializer=None):
        self.socket = ZmqSocket(host=host, port=port, mode=zmq.PULL, bind=bind)
        self.serializer = serializer
        self.socket.establish()

    def pull(self):
        data = self.socket.recv()
        if self.serializer:
            data = self.serializer(data)
        return data


class ZmqClient:
    """
    Send request and receive reply from ZmqServer
    """
    def __init__(self, host, port, timeout=-1,
                 serializer=None, deserializer=None):
        """
        Args:
            timeout: how long do we wait for response, in seconds,
               negative means wait indefinitely
        """
        self.timeout = timeout
        self.host = host
        self.port = int(port)
        self.serializer = serializer
        self.deserializer = deserializer
        self.socket = ZmqSocket(
            host=self.host, port=self.port, mode=zmq.REQ, bind=False
        )
        if self.timeout >= 0:
            self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.establish()

    def request(self, msg):
        """
        Requests to the earlier provided host and port for data.

        https://github.com/zeromq/pyzmq/issues/132
        We allow the requester to time out

        Args:
            msg: send msg to ZmqServer to request for reply

        Returns:
            reply data from ZmqServer

        Raises:
            ZmqTimeoutError if timed out
        """

        if self.serializer:
            msg = self.serializer(msg)

        self.socket.send(msg)

        if self.timeout >= 0:
            poller = zmq.Poller()
            poller.register(self.socket.unwrap(), zmq.POLLIN)
            if poller.poll(self.timeout * 1000):
                rep = self.socket.recv()
                if self.deserializer:
                    rep = self.deserializer(rep)
                return rep
            else:
                raise ZmqTimeoutError()
        else:
            rep = self.socket.recv()
            if self.deserializer:
                rep = self.deserializer(rep)
            return rep


class ZmqServer:
    def __init__(self, host, port,
                 serializer=None,
                 deserializer=None,
                 load_balanced=False,
                 context=None):
        """
        Args:
            host:
            port:
            load_balanced:
            serializer: serialize data before replying (sending)
            deserializer: deserialize data after receiving
            context:

        """
        self.host = host
        self.port = int(port)
        self.serializer = serializer
        self.deserializer = deserializer
        self.socket = ZmqSocket(
            mode=zmq.REP,
            host=self.host,
            port=self.port,
            bind=not load_balanced,
            context=context
        )
        self.socket.establish()
        self._thread = None
        self._next_step = 'recv'  # for error checking only

    def recv(self):
        if self._next_step != 'recv':
            raise ValueError('recv() and send() must be paired. You can only send() now')
        data = self.socket.recv()
        if self.deserializer:
            data = self.deserializer(data)
        self._next_step = 'send'
        return data

    def send(self, msg):
        if self._next_step != 'send':
            raise ValueError('send() and recv() must be paired. You can only recv() now')
        if self.serializer:
            msg = self.serializer(msg)
        self.socket.send(msg)
        self._next_step = 'recv'

    def _event_loop(self, handler):
        while True:
            msg = self.recv()  # request msg from ZmqClient
            reply = handler(msg)
            self.send(reply)

    def start_event_loop(self, handler, blocking=False):
        """
        Args:
            handler: function that takes an incoming client message (deserialized)
                and returns a reply to client (before serializing)
            blocking: True to block the main program
                False to launch a thread in the background and immediately returns

        Returns:
            if non-blocking, returns the created thread
        """
        if blocking:
            self._event_loop(handler)
        else:
            if self._thread:
                raise RuntimeError('event loop is already running')
            self._thread = start_thread(self._event_loop)
            return self._thread

# TODO
# ========================================================
# Everything after this needs refactoring
# ========================================================


class ZmqReqWorker(Thread):
    """
        Requests to 'inproc://worker' to get request data
        Sends requests to 'tcp://@host:@port'
        Gives response to @handler
    """
    def __init__(self, context, host, port, handler):
        Thread.__init__(self)
        self.context = context
        
        self.sw_out = ZmqSocket(host=host, port=port,
                                mode=zmq.REQ, bind=False, context=context)

        self.sw_inproc = ZmqSocket(address='inproc://worker', mode=zmq.REQ,
                                   bind=False, context=context)
        self.handler = handler

    def run(self):
        self.out_socket = self.sw_out.establish()
        self.task_socket = self.sw_inproc.establish()
        while True:
            self.task_socket.send(b'ready')
            request = self.task_socket.recv()
            
            self.out_socket.send(request)
            response = self.out_socket.recv()
            self.handler(response)

        # Never reaches here
        self.out_socket.close()
        self.task_socket.close()

class ZmqReqClientPool(Thread):
    """
        Spawns num_workers threads and send requests to the provided endpoint
        Responses are given to @handler
    """
    def __init__(self, host, port, handler, num_workers=5):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.handler = handler
        self.num_workers = num_workers

    def get_request(self):
        raise NotImplementedError

    def run(self):
        context = zmq.Context()
        router = context.socket(zmq.ROUTER)
        router.bind("inproc://worker")

        workers = []
        for worker_id in range(self.num_workers):
            worker = ZmqReqWorker(context,
                                    self.host,
                                    self.port,
                                    self.handler)
            worker.start()
            workers.append(worker)

        # Distribute all tasks 
        while True:
            request = self.get_request()
            address, empty, ready = router.recv_multipart()
            router.send_multipart([address, b'', request])

        # Never reach
        router.close()
        context.term()


class ZmqReqClientPoolFixedRequest(ZmqReqClientPool):
    """
        Always blasts the same request
    """
    def __init__(self, host, port, handler, request, num_workers=5):
        super().__init__(host, port, handler, num_workers)
        self.request = request

    def get_request(self):
        return self.request


class ZmqPub(ZmqSocket):
    def __init__(self, host, port, hwm=1, serializer=None):
        super().__init__(host=host, port=port, mode=zmq.PUB, bind=True)
        self._socket.set_hwm(hwm)
        self.serializer = serializer
        self.establish()

    def pub(self, topic, data):
        topic = str2bytes(topic)
        if self.serializer:
            data = self.serializer(data)
        self._socket.send_multipart([topic, data])


class ZmqSub(ZmqSocket):
    def __init__(self, host, port, topic, hwm=1, serializer=None, context=None):
        super().__init__(host=host, port=port, mode=zmq.SUB, bind=False, context=context)
        topic = str2bytes(topic)
        self.topic = topic
        self._socket.set_hwm(hwm)
        self._socket.setsockopt(zmq.SUBSCRIBE, topic)
        self.serializer = serializer
        self.establish()

    def recv(self):
        topic, data = self._socket.recv_multipart()
        if self.serializer:
            data = self.serializer(data)
        return data


class ZmqSubClient(Thread):
    def __init__(self, host, port, topic, handler, serializer=None, hwm=1, context=None):
        Thread.__init__(self)
        self.hwm = hwm
        self.host = host
        self.port = port
        self.topic = topic
        self.serializer = serializer
        self.handler = handler
        self.context = context

    def run(self):
        self.sub = ZmqSub(self.host, self.port, self.topic, self.hwm, context=self.context)
        # zmq_logger.infofmt('SubClient listening for topic {} on {}:{}', 
                             # self.topic, self.host, self.port)
        while True:
            data = self.sub.recv()
            if self.serializer:
                data = self.serializer(data)
            self.handler(data)


class ZmqAsyncServerWorker(Thread):
    """
    replay -> learner, replay handling learner's requests
    """
    def __init__(self, context, handler, serializer, deserializer):
        Thread.__init__(self)
        self.context = context
        self._handler = handler
        self.serializer = serializer
        self.deserializer = deserializer

    def run(self):
        socket = self.context.socket(zmq.REP)
        socket.connect('inproc://worker')
        while True:
            req = socket.recv()
            if self.serializer:
                req = self.serializer(req)
            res = self._handler(req)
            if self.deserializer:
                res = self.deserializer(res)
            socket.send(res)
        socket.close()


class ZmqAsyncServer(Thread):
    """
    replay -> learner, manages ZmqServerWorker pool
    Async REQ-REP server
    """
    def __init__(self, host, port, handler, num_workers=1,
                    load_balanced=False, serializer=None, deserializer=None):
        """
        Args:
            port:
            handler: takes the request (pyobj) and sends the response
        """
        Thread.__init__(self)
        self.port = port
        self.host = host
        self.handler = handler
        self.num_workers = num_workers
        self.load_balanced = load_balanced
        self.serializer = serializer
        self.deserializer = deserializer

    def run(self):
        context = zmq.Context()
        router_sw = ZmqSocket(mode=zmq.ROUTER,
                              bind=(not self.load_balanced),
                              host=self.host,
                              port=self.port,
                              context=context)
        router = router_sw.establish()

        dealer_sw = ZmqSocket(mode=zmq.ROUTER,
                              bind=True,
                              address="inproc://worker",
                              context=context)
        dealer = dealer_sw.establish()

        workers = []
        for worker_id in range(self.num_workers):
            worker = ZmqAsyncServerWorker(context, self.handler, self.serializer, self.deserializer)
            worker.start()
            workers.append(worker)

        # http://zguide.zeromq.org/py:mtserver
        # http://api.zeromq.org/3-2:zmq-proxy
        # **WARNING**: zmq.proxy() must be called AFTER the threads start,
        # otherwise the program hangs!
        # Before calling zmq_proxy() you must set any socket options, and
        # connect or bind both frontend and backend sockets.
        zmq.proxy(router, dealer)
        # should never reach
        router.close()
        dealer.close()
        context.term()


class ZmqSimpleServer(Thread):
    def __init__(self, host, port, handler,
                 load_balanced, context=None,
                 serializer=None, 
                 deserializer=None):
        Thread.__init__(self)
        self.host = host
        self.port = port
        self.bind = (not load_balanced)
        self.serializer = serializer
        self.deserializer = deserializer
        self.handler = handler
        self.context = context

    def run(self):
        self.sw = ZmqSocket(mode=zmq.REP,
                            host=self.host,
                            port=self.port,
                            bind=self.bind,
                            context=self.context)
        socket = self.sw.establish()
        while True:
            req = socket.recv()
            if self.serializer:
                req = self.serializer(req)
            res = self.handler(req)
            if self.deserializer:
                res = self.deserializer(res)
            socket.send(res)
