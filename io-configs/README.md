## Overview
DATABASE and API to provide configurations for I/O

Configurations are storied in AWS dynamoDB tables and can be accessed via a RESTful API.

Uses AWS Lambda, invoked by changes to dynamoDB to trigger redis messages regarding updates to associated apps.

Deployed to `API_GATEWAY_HERE`

## Endpoints

There are two kinds of endpoints. The first type returns data intended to be used to configure I/O applications. The second type are the CRUD endpoints needed to maintain the data needed to create the first type of request. The second type of endpoints will be called by the tools used by admins and partners to maintain the configurations.


**Organizatioon and description of tables, schema, endpoints continue in actual README.**
 

# Development

## Environment setup

### Required environment variables

- API_KEY--the key that will be used for authentication when accessing the API
- FLASK_ENV--which mode to run the Flask application in (prod or debug)
- READ_ONLY_MODE--whether or not writing to the database should occur

### Optional environment variables

- DYNAMO_HOST--DDB host to use (should only be used with DynamoDBLocal)
- AWS_REGION--which AWS region to use (defaults to us-east-1)


## DynamoDB setup

By default, this application will interact with AWS DDB tables in the configured region.
To run with DynamoDBLocal:

- Download and install the tool (https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html)
- Start it up
- ``export DYNAMO_HOST=http://localhost:8000``
- Run this application in one of the ways listed below


## Running the app

### Simple Flask app

Working in a virtual environment with the appropriate requirements installed, run

``python application.py``


### Docker
To run the using docker, run `docker-compose up --build` in the main folder. Make sure you have already configured AWS CLI on your local machine (https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html). Changes made to `application.py` or in the `config` folder will trigger a reload of the server. If you are running the react client, you'll want to change the `REACT_APP_API_URL` in `.env.development` to `http://localhost:5000/`. Please don't commit this change. Run `docker-compose down` after you are finished to shutdown the container.

Important:
- Any calls to resources in a VPC (like websites) will not work when you are running this locally.
- If you have an error in your python syntax, the docker logs will stop, but the container will restart after you fix the error. This seems to be a quirk of docker. If you run `docker ps` you can still see the container running. Just make sure you run `docker-compose down` after you are finished.
