from pytest import fixture, raises
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_pool import WrapperPool


@fixture(scope="function")
def wrapper():
    return WrapperPool(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2))


def test_initial_state(wrapper: WrapperPool):
    assert wrapper.get_total_value() == 0
    assert wrapper.get_total_shares() == 0
    assert wrapper.assets_of("user") == 0
    assert wrapper.balance_of("user") == 0


def test_stake_increase_total_value(wrapper: WrapperPool):
    new_stake = 1000

    total_value_before = wrapper.get_total_value()
    wrapper.stake_eth("user", new_stake)
    total_value_after = wrapper.get_total_value()

    assert total_value_after == total_value_before + new_stake


def test_stake_increase_total_shares(wrapper: WrapperPool):
    new_stake = 1000

    total_shares_before = wrapper.get_total_shares()
    wrapper.stake_eth("user", new_stake)
    total_shares_after = wrapper.get_total_shares()

    assert total_shares_after == total_shares_before + new_stake


def test_stake_increase_user_assets(wrapper: WrapperPool):
    new_stake = 1000

    assets_before = wrapper.assets_of("user")
    wrapper.stake_eth("user", new_stake)
    assets_after = wrapper.assets_of("user")

    assert assets_after == assets_before + new_stake


def test_stake_increase_user_balance(wrapper: WrapperPool):
    new_stake = 1000

    balance_before = wrapper.balance_of("user")
    wrapper.stake_eth("user", new_stake)
    balance_after = wrapper.balance_of("user")

    assert balance_after == balance_before + new_stake


def test_revert_on_stake_zero(wrapper: WrapperPool):
    with raises(Exception):
        wrapper.stake_eth("user", 0)


def test_revert_on_stake_negative(wrapper: WrapperPool):
    with raises(Exception):
        wrapper.stake_eth("user", -1)


def test_rewards_increase_user_assets(wrapper: WrapperPool):
    eth_to_stake, rewards = 100, 20
    wrapper.stake_eth("user", eth_to_stake)

    wrapper.vault.increase_total_value(rewards)
    assert wrapper.assets_of("user") == eth_to_stake + rewards
    assert wrapper.balance_of("user") == eth_to_stake
