"""In-memory adapter binding for the shared repository contract suite."""

import pytest

from battle_hexes_api.persistence import GameRepositoryInMemory
from tests.test_game_repository_contract import RepositoryContractTests


class TestGameRepositoryInMemory(RepositoryContractTests):
    @pytest.fixture
    def repository_factory(self):
        return GameRepositoryInMemory
