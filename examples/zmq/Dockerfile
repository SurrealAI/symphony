from python:3.6

RUN echo cache bust 125
COPY symphony /symphony
RUN pip install pyzmq pyarrow
RUN pip install -e /symphony/ && \ 
	cp /symphony/examples/zmq/run_simple_client.py /run_simple_client.py && \
	cp /symphony/examples/zmq/run_simple_server.py /run_simple_server.py 