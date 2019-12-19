# build output folder
OUTPUTFOLDER = dist
# docker image
DOCKER_REGISTRY = apeunit
DOCKER_IMAGE = aepp-faucet
K8S_DEPLOYMENT = aepp-faucet
K8S_NAMESPACE = testnet
DOCKER_TAG = $(shell git describe --always)
# build paramters
OS = linux
ARCH = amd64
# k8s parameters


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

docker-build:
	@echo build image
	npm install
	npm run prod
	docker build -t $(DOCKER_IMAGE) -f Dockerfile .
	@echo done

docker-push:
	@echo push image
	docker tag $(DOCKER_IMAGE) $(DOCKER_REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	aws ecr get-login --no-include-email --region eu-central-1 --profile aeternity-sdk | sh
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



docker-run:
	@docker run -p 5000:5000 $(DOCKER_IMAGE)

debug-start:
	. .envrc
	python3 faucet.py start
