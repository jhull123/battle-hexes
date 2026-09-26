"""Build stable low-level DynamoDB transaction requests."""


def create_transaction(table_name, game_item, receipt_item, now):
    values = {":now": {"N": str(now)}}
    condition = "attribute_not_exists(pk) OR ttl <= :now"
    return {
        "TransactItems": [
            {"Put": {"TableName": table_name, "Item": game_item,
                     "ConditionExpression": condition,
                     "ExpressionAttributeValues": values}},
            {"Put": {"TableName": table_name, "Item": receipt_item,
                     "ConditionExpression": condition,
                     "ExpressionAttributeValues": values}},
        ],
    }


def commit_transaction(
    table_name, game_key, game_item, receipt_item, expected_version, now
):
    names = {f"#{name}": name for name in _MUTABLE_GAME_ATTRIBUTES}
    assignments = ", ".join(
        f"#{name} = :{name}" for name in _MUTABLE_GAME_ATTRIBUTES
    )
    values = {
        f":{name}": game_item[name]
        for name in _MUTABLE_GAME_ATTRIBUTES
    }
    values.update({
        ":expected_version": {"N": str(expected_version)},
        ":now": {"N": str(now)},
    })
    receipt_values = {":now": {"N": str(now)}}
    return {
        "TransactItems": [
            {"Update": {
                "TableName": table_name,
                "Key": game_key,
                "UpdateExpression": f"SET {assignments}",
                "ConditionExpression": (
                    "#version = :expected_version AND #ttl > :now"
                ),
                "ExpressionAttributeNames": names,
                "ExpressionAttributeValues": values,
            }},
            {"Put": {
                "TableName": table_name,
                "Item": receipt_item,
                "ConditionExpression": (
                    "attribute_not_exists(pk) OR ttl <= :now"
                ),
                "ExpressionAttributeValues": receipt_values,
            }},
        ],
    }


_MUTABLE_GAME_ATTRIBUTES = (
    "item_type", "game_id", "version", "state_schema_version",
    "scenario_id", "scenario_version", "state", "updated_at", "ttl",
)
