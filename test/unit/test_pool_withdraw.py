from pytest import fixture, raises
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_pool import WrapperPool

user1_initial_eth = 100_000
user2_initial_eth = 100_000


@fixture(scope="function")
def wrapper():
    wrapper = WrapperPool(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2))
    wrapper.stake_eth("user1", user1_initial_eth)
    wrapper.stake_eth("user2", user2_initial_eth)
    return wrapper


def test_initial_state(wrapper: WrapperPool):
    assert wrapper.get_total_value() == user1_initial_eth + user2_initial_eth
    assert wrapper.get_total_shares() == user1_initial_eth + user2_initial_eth
    assert wrapper.assets_of("user1") == user1_initial_eth
    assert wrapper.balance_of("user1") == user1_initial_eth
    assert wrapper.assets_of("user2") == user2_initial_eth
    assert wrapper.balance_of("user2") == user2_initial_eth


def test_withdraw_from_user_decreases_total_value_and_shares(wrapper: WrapperPool):
    wrapper.withdraw_eth("user1", user1_initial_eth)

    assert wrapper.get_total_value() == user2_initial_eth
    assert wrapper.get_total_shares() == user2_initial_eth


def test_withdraw_from_user_decreases_balance_and_assets(wrapper: WrapperPool):
    wrapper.withdraw_eth("user1", user1_initial_eth)

    assert wrapper.balance_of("user1") == 0
    assert wrapper.assets_of("user1") == 0


def test_revert_on_withdraw_zero(wrapper: WrapperPool):
    with raises(Exception):
        wrapper.withdraw_eth("user1", 0)


def test_revert_on_withdraw_negative(wrapper: WrapperPool):
    with raises(Exception):
        wrapper.withdraw_eth("user1", -1)


def test_revert_on_withdraw_more_than_balance(wrapper: WrapperPool):
    with raises(Exception):
        wrapper.withdraw_eth("user1", user1_initial_eth + 1)


def test_withdraw_after_rebase(wrapper: WrapperPool):
    rewards = 20_000
    wrapper.vault.increase_total_value(rewards)

    assert wrapper.balance_of("user1") == user1_initial_eth
    assert wrapper.assets_of("user1") == user1_initial_eth + rewards // 2

    wrapper.withdraw_eth("user1", user1_initial_eth + rewards // 2)

    assert wrapper.balance_of("user1") == 0
    assert wrapper.assets_of("user1") == 0

    assert wrapper.get_total_value() == user2_initial_eth + rewards // 2
    assert wrapper.get_total_shares() == user2_initial_eth


def test_withdraw_partial(wrapper: WrapperPool):
    withdraw_amount = 30_000
    wrapper.withdraw_eth("user1", withdraw_amount)

    assert wrapper.balance_of("user1") == user1_initial_eth - withdraw_amount
    assert wrapper.assets_of("user1") == user1_initial_eth - withdraw_amount
