"""Opt-in repository contract against a disposable local DynamoDB table.

Set DYNAMODB_TEST_ENDPOINT_URL to a DynamoDB Local-compatible loopback URL.
Each test creates and deletes its own table; no AWS account is used.
"""

import os
from urllib.parse import urlparse
from uuid import uuid4

import boto3
import pytest

from battle_hexes_api.persistence import GameRepositoryDynamoDB
from tests.test_game_repository_contract import RepositoryContractTests


class TestGameRepositoryDynamoDBLocal(RepositoryContractTests):
    @pytest.fixture
    def repository_factory(self):
        endpoint = os.environ.get("DYNAMODB_TEST_ENDPOINT_URL")
        if not endpoint:
            pytest.skip("set DYNAMODB_TEST_ENDPOINT_URL for integration tests")
        parsed = urlparse(endpoint)
        if (parsed.scheme not in ("http", "https")
                or parsed.hostname not in ("localhost", "127.0.0.1", "::1")):
            pytest.fail("DYNAMODB_TEST_ENDPOINT_URL must be loopback")

        client = boto3.client(
            "dynamodb",
            endpoint_url=endpoint,
            region_name="us-east-1",
            aws_access_key_id="local",
            aws_secret_access_key="local",
        )
        table_name = "battle-hexes-test-" + uuid4().hex
        client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {"AttributeName": "pk", "AttributeType": "S"},
                {"AttributeName": "sk", "AttributeType": "S"},
            ],
            KeySchema=[
                {"AttributeName": "pk", "KeyType": "HASH"},
                {"AttributeName": "sk", "KeyType": "RANGE"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        try:
            client.get_waiter("table_exists").wait(TableName=table_name)

            def make_repository(clock, sizer, budget):
                return GameRepositoryDynamoDB(
                    table_name, client, clock, sizer, budget
                )
            yield make_repository
        finally:
            client.delete_table(TableName=table_name)
