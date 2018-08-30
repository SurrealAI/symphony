FROM python:3.6
RUN pip install pyzmq pyarrow

# change this line to force update image
RUN echo cache bust 123
COPY symphony /symphony
COPY caraml /caraml
RUN pip install -e /symphony/
RUN pip install -e /caraml/
COPY /symphony/examples/zmq_nfs/run_simple_client.py /run_simple_client.py
COPY /symphony/examples/zmq_nfs/run_simple_server.py /run_simple_server.py
COPY /symphony/examples/zmq_nfs/nfs_settings.py /nfs_settings.py
