from datetime import datetime
from typing import Iterator, List
from unittest import TestCase

import pytest
from freezegun import freeze_time
from freezegun.api import FakeDatetime

@freeze_time("2022-10-01")
class TestClassDecoratorWithFixture:
    @pytest.fixture
    def ff(self) -> datetime:
        return datetime.now()

    def test_with_fixture(self, ff: datetime) -> None:
        assert ff == FakeDatetime(2022, 10, 1, 0, 0)
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)

    def test_without_fixture(self) -> None:
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)


@freeze_time("2022-10-01")
class TestClassDecoratorWithYieldFixture:
    teardown_times: List[datetime] = []

    @pytest.fixture
    def ff(self) -> Iterator[datetime]:
        setup_time = datetime.now()
        yield setup_time
        self.teardown_times.append(datetime.now())

    def test_with_fixture(self, ff: datetime) -> None:
        assert ff == FakeDatetime(2022, 10, 1, 0, 0)
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)

    def test_fixture_teardown_ran_with_frozen_time(self) -> None:
        assert self.teardown_times == [FakeDatetime(2022, 10, 1, 0, 0)]
