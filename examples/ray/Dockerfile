FROM us.gcr.io/surreal-dev-188523/surreal-cpu:latest

RUN pip install ray benedict gym[atari]
RUN pip install docker

# for weird Ray command encoding issue
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# force cache bust after this line
RUN echo cache bust 124
RUN pip install git+git://github.com/SurrealAI/nanolog.git
COPY examples/ray/entry.py /mylibs
RUN chmod +x /mylibs/entry.py

RUN mkdir /mylibs/symphony
COPY . /mylibs/symphony
RUN pip install -e /mylibs/symphony

WORKDIR /root
#RUN mkdir ray
COPY examples/ray /root/
ENTRYPOINT ["/mylibs/entry.py"]
