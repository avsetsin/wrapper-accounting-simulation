from pytest import fixture
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


def test_rewards_increase_user_assets(wrapper: WrapperPool):
    rewards = 20_000
    wrapper.vault.increase_total_value(rewards)

    assert wrapper.assets_of("user1") == user1_initial_eth + rewards // 2
    assert wrapper.assets_of("user2") == user2_initial_eth + rewards // 2
