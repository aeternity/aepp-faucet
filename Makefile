# docker image
DOCKER_REGISTRY ?= docker.io
DOCKER_IMAGE ?= aeternity/aepp-faucet
K8S_DEPLOYMENT ?= aepp-faucet
K8S_NAMESPACE ?= testnet
DOCKER_TAG ?= $(shell git describe --always)
# build paramters
OS = linux
ARCH = amd64

.PHONY: list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs

clean:
	@echo remove generated folders
	rm -rf frontend/templates frontend/assets frontend/node_modules node_modules
	@echo done

docker-build:
	@echo build image
	docker build -t $(DOCKER_IMAGE) -f Dockerfile .
	@echo done

docker-run:
	@docker run -p 5000:5000 -e FAUCET_ACCOUNT_PRIV_KEY=$(FAUCET_ACCOUNT_PRIV_KEY) $(DOCKER_IMAGE)

docker-push:
	@echo push image
	docker tag $(DOCKER_IMAGE) $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo done

k8s-deploy:
	@echo deploy k8s
	kubectl -n $(K8S_NAMESPACE) set image deployment/$(K8S_DEPLOYMENT) $(DOCKER_IMAGE)=$(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	@echo done

k8s-rollback:
	@echo deploy k8s
	kubectl -n $(K8S_NAMESPACE) rollout undo deployment/$(K8S_DEPLOYMENT)
	@echo done
