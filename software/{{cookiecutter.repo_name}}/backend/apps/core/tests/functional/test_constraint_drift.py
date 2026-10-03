"""Every rule a model declares exists in Postgres, under the same name.

A migration edited by hand, or a constraint dropped in the database, would
otherwise leave the model promising a rule that nothing enforces.
"""

import pytest
from django.apps import apps
from django.db import connection


def _declared() -> dict[str, set[str]]:
    return {
        model._meta.db_table: {rule.name for rule in model._meta.constraints}
        for model in apps.get_models()
        if model._meta.app_config.name.startswith("apps.")
        and model._meta.constraints
    }


def _catalogue(table: str) -> set[str]:
    # Unique constraints over expressions are unique indexes in Postgres.
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT conname FROM pg_constraint WHERE conrelid = %s::regclass"
            " UNION SELECT indexname FROM pg_indexes WHERE tablename = %s",
            [table, table],
        )
        return {row[0] for row in cursor.fetchall()}


def missing_rules() -> dict[str, set[str]]:
    """Return each table's declared rules that Postgres does not have."""
    gaps = {
        table: names - _catalogue(table)
        for table, names in _declared().items()
    }
    return {table: names for table, names in gaps.items() if names}


@pytest.mark.django_db
def test_every_declared_rule_is_in_postgres() -> None:
    assert missing_rules() == {}


@pytest.mark.django_db
def test_a_dropped_rule_is_reported() -> None:
    # The test's transaction rolls the DROP back; DDL is transactional in
    # Postgres.
    declared = _declared()
    if not declared:
        pytest.skip("no app declares a rule yet")
    table = sorted(declared)[0]
    name = sorted(declared[table])[0]
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_constraint WHERE conname = %s", [name]
        )
        is_constraint = cursor.fetchone() is not None
        quoted = connection.ops.quote_name(name)
        if is_constraint:
            table_name = connection.ops.quote_name(table)
            cursor.execute(
                f"ALTER TABLE {table_name} DROP CONSTRAINT {quoted}"
            )
        else:
            cursor.execute(f"DROP INDEX {quoted}")
    assert missing_rules() == {table: {name}}
