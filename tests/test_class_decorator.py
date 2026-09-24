from datetime import datetime
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


yield_fixture_events = []


@freeze_time("2022-10-01")
class TestClassDecoratorWithYieldFixture:
    @pytest.fixture
    def ff(self):
        yield_fixture_events.append(("setup", datetime.now()))
        yield datetime.now()
        yield_fixture_events.append(("teardown", datetime.now()))

    def test_with_yield_fixture(self, ff: datetime) -> None:
        assert ff == FakeDatetime(2022, 10, 1, 0, 0)
        assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)

    def test_yield_fixture_setup_and_teardown_ran_frozen(self) -> None:
        assert yield_fixture_events == [
            ("setup", FakeDatetime(2022, 10, 1, 0, 0)),
            ("teardown", FakeDatetime(2022, 10, 1, 0, 0)),
        ]


module_yield_fixture_events = []


@pytest.fixture
def module_yield_fixture():
    module_yield_fixture_events.append("setup")
    yield 42
    module_yield_fixture_events.append("teardown")


@freeze_time("2022-10-01")
def test_function_decorator_with_yield_fixture(module_yield_fixture) -> None:
    assert module_yield_fixture == 42
    assert datetime.now() == FakeDatetime(2022, 10, 1, 0, 0)


def test_module_yield_fixture_setup_and_teardown_ran() -> None:
    assert module_yield_fixture_events == ["setup", "teardown"]
