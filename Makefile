SHELL:=/bin/bash

.PHONY: help


help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

setenv: ## Setting deploy environement values
	TMP_PROJECT=$(shell gcloud config list --format 'value(core.project)'); \
	read -e -p "Enter Your Project Name: " -i $${TMP_PROJECT} PROJECT_ID; \
	gcloud config set project $${PROJECT_ID}; \
	read -e -p "Enter Desired Cloud Run Region: " -i 'europe-west1' CLOUD_RUN_REGION; \
	gcloud config set run/region $${CLOUD_RUN_REGION}; \
	read -e -p "Enter Desired Cloud Run Platform: " -i 'managed' CLOUD_RUN_PLATFORM; \
	gcloud config set run/platform $${CLOUD_RUN_PLATFORM};

init-users:
	gcloud iam service-accounts create ${{xia.sa-name}} \
		--display-name "Cloud Run Insight Cleaner";

init-roles:
	@PROJECT_ID=$(shell gcloud config list --format 'value(core.project)'); \
	gcloud projects add-iam-policy-binding $${PROJECT_ID} \
		--member=serviceAccount:${{xia.sa-name}}@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/logging.logWriter; \
	gcloud projects add-iam-policy-binding $${PROJECT_ID} \
		--member=serviceAccount:${{xia.sa-name}}@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/${{xia.db-role}};

build:
	PROJECT_ID=$(shell gcloud config list --format 'value(core.project)'); \
	gcloud builds submit --tag gcr.io/$${PROJECT_ID}/${{xia.serivce-name}};

deploy:
	PROJECT_ID=$(shell gcloud config list --format 'value(core.project)'); \
	CLOUD_RUN_REGION=$(shell gcloud config list --format 'value(run.region)'); \
	CLOUD_RUN_PLATFORM=$(shell gcloud config list --format 'value(run.platform)'); \
	gcloud run deploy ${{xia.service-name}} \
		--image gcr.io/$${PROJECT_ID}/${{xia.serivce-name}} \
    	--service-account ${{xia.sa-name}}@$${PROJECT_ID}.iam.gserviceaccount.com \
		--region $${CLOUD_RUN_REGION} \
		--platform $${CLOUD_RUN_PLATFORM} \
		--no-allow-unauthenticated; \
	gcloud run services add-iam-policy-binding ${{xia.serivce-name}} \
		--member=serviceAccount:cloud-run-pubsub-invoker@$${PROJECT_ID}.iam.gserviceaccount.com \
		--role=roles/run.invoker \
		--region $${CLOUD_RUN_REGION} \
		--platform $${CLOUD_RUN_PLATFORM};