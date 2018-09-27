GIT_DESCR = $(shell git describe --always) 
# build output folder
OUTPUTFOLDER = dist
# docker image
DOCKER_IMAGE = 166568770115.dkr.ecr.eu-central-1.amazonaws.com/aeternity/aepp-faucet
DOCKER_TAG = $(shell git describe --always)
# build paramters
OS = linux
ARCH = amd64

.PHONY: list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs


lint: lint-all

lint-all:
	flake8

clean:
	@echo remove $(OUTPUTFOLDER) folder
	@rm -rf dist
	@echo done

docker: docker-build

docker-build:
	@echo build image
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) -f Dockerfile .
	@echo done

docker-push: docker-build
	@echo push image
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)
  docker push $(DOCKER_IMAGE):latest
	@echo done

docker-run: 
	@docker run -p 5000:5000 $(DOCKER_IMAGE) 

debug-start:
	@python3 faucet.py start
