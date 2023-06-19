SHELL := /bin/bash


.PHONY: help
help:
	@printf "available targets -->\n\n"
	@cat Makefile | grep ".PHONY" | grep -v ".PHONY: _" | sed 's/.PHONY: //g'


env.sh:
	wget https://raw.githubusercontent.com/daxxog/envsubst-mustache/caaf2b3ee50e7e1d64a6dfca0b3ef44473c24437/env.sh


.gitignore:
	echo '/env/' > .gitignore


.python-version:
	curl -sL \
		https://raw.githubusercontent.com/docker-library/python/master/3.$$( \
			curl -sL \
				https://raw.githubusercontent.com/docker-library/python/master/versions.json \
				| yq keys -o tsv \
				| tr '\t' '\n' \
				| grep -v rc \
				| grep '3.' \
				| sed 's/3\.//g' \
				| sort -n \
				| tail -n 1 \
		)/bullseye/Dockerfile \
		| grep PYTHON_VERSION \
		| head -n 1 \
		| sed 's/ENV PYTHON_VERSION//g; s/ //g' \
		| tee .python-version \
	;


env: env.sh .python-version requirements.dev.txt .gitignore
	bash -c 'source env.sh'


requirements.dev.in:
	echo pip-tools > requirements.dev.in
	echo poetry >> requirements.dev.in


requirements.dev.txt: requirements.dev.in env.sh .python-version
	if [ ! -d env ]; then \
		bash <(cat env.sh | grep -v 'requirements.dev.txt' | grep -v 'poetry install') \
		&& bash -c 'source env/bin/activate && set -x && which python3 && python3 -m pip install -r requirements.dev.in' \
		&& bash -c 'source env/bin/activate && set -x && pip-compile --generate-hashes --resolver=backtracking requirements.dev.in' \
		&& rm -rf env; \
	else \
		echo please remove the env folder before bootstrapping requirements.dev.txt; \
		exit 1; \
	fi


poetry.lock: env pyproject.toml
	bash -c 'source env.sh && set -x && poetry install'


.PHONY: lint
lint: env .pre-commit-config.yaml
	bash -c 'source env.sh && lint'


swagger/gitea:
	mkdir -p ./swagger/gitea


swagger/gitea/swagger.v1.json: swagger/gitea
	curl -sL https://try.gitea.io/swagger.v1.json > ./swagger/gitea/swagger.v1.json


openapi:
	mkdir -p openapi


openapi/gitea.yaml: openapi swagger/gitea/swagger.v1.json
	podman run \
		-i \
		-t \
		--entrypoint /usr/local/openjdk-11/bin/java \
		-v "$$(pwd)/openapi":/mnt/openapi \
		-v "$$(pwd)/swagger":/mnt/swagger \
		openapitools/openapi-generator-cli:v6.6.0 \
		-jar /opt/openapi-generator/modules/openapi-generator-cli/target/openapi-generator-cli.jar \
		generate \
		-g openapi-yaml \
		-i /mnt/swagger/gitea/swagger.v1.json \
		-o /mnt/openapi/gitea.yaml \
	;


src/gitea_docker_cleanup/models:
	mkdir -p ./src/gitea_docker_cleanup/models


src/gitea_docker_cleanup/models/gitea.py: openapi/gitea.yaml env src/gitea_docker_cleanup/models
	bash -c 'source env.sh && set -x && datamodel-codegen --input openapi/gitea.yaml/openapi/openapi.yaml > src/gitea_docker_cleanup/models/gitea.py'
