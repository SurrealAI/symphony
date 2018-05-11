FROM us.gcr.io/surreal-dev-188523/surreal-cpu:latest

RUN pip install ray benedict gym[atari]

# for weird Ray command encoding issue
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY entry.py /mylibs
RUN chmod +x /mylibs/entry.py

WORKDIR /root
#RUN mkdir ray
COPY . /root/
ENTRYPOINT ["/mylibs/entry.py"]
