FROM us.gcr.io/surreal-dev-188523/surreal-cpu:latest

COPY entry.py /mylibs
RUN chmod +x /mylibs/entry.py

WORKDIR /root
RUN mkdir ray
COPY . /root/ray/
ENTRYPOINT ["/mylibs/entry.py"]
