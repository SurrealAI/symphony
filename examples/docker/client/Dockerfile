FROM python:3.6
COPY . /symphony
RUN pip install pyzmq pyarrow
RUN pip install -e /symphony/
WORKDIR /symphony/examples/docker
ENTRYPOINT ["python", "client/run_client.py"]
