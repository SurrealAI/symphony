cpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-cpu'
gpu_image = 'us.gcr.io/surreal-dev-188523/jimfan-gpu'


build:
	# build from symphony/ repo root folder
	docker build -t $(cpu_image):latest -f Dockerfile ../../

_push:
	docker push $(cpu_image):latest

push: build _push

