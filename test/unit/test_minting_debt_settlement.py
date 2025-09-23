from pytest import fixture, approx
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting

TOLERANCE = 2  # due to rounding

user1_initial_eth = 100_000
user2_initial_eth = 100_000

user1_minted_steth = 50_000
user2_minted_steth = 50_000


@fixture(scope="function")
def wrapper():
    wrapper = WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)
    wrapper.stake_eth("user1", user1_initial_eth)
    wrapper.stake_eth("user2", user2_initial_eth)
    wrapper.mint_steth("user1", user1_minted_steth)
    wrapper.mint_steth("user2", user2_minted_steth)

    return wrapper


def test_initial_state(wrapper: WrapperMinting):
    assert wrapper.get_total_value() == user1_initial_eth + user2_initial_eth
    assert wrapper.get_total_shares() == user1_initial_eth + user2_initial_eth
    assert wrapper.assets_of("user1") == user1_initial_eth
    assert wrapper.balance_of("user1") == user1_initial_eth
    assert wrapper.assets_of("user2") == user2_initial_eth
    assert wrapper.balance_of("user2") == user2_initial_eth
    assert wrapper.minted_liability_steth("user1") == user1_minted_steth
    assert wrapper.minted_liability_steth("user2") == user2_minted_steth


def test_rebalance_decrease_total_value(wrapper: WrapperMinting):
    total_value_before = wrapper.get_total_value()
    liability_wsteth = wrapper.minted_liability_wsteth("user1")
    liability_steth = wrapper.minted_liability_steth("user1")

    wrapper.vault_rebalance_minted_liability_wsteth("user1", liability_wsteth)
    assert wrapper.get_total_value() == approx(total_value_before - liability_steth, TOLERANCE)


def test_rebalance_decrease_total_liability(wrapper: WrapperMinting):
    total_liability_before = wrapper.get_total_minted_liability_wsteth()
    liability_wsteth = wrapper.minted_liability_wsteth("user1")

    wrapper.vault_rebalance_minted_liability_wsteth("user1", liability_wsteth)
    assert wrapper.get_total_minted_liability_wsteth() == total_liability_before - liability_wsteth


def test_rebalance_decrease_user_assets(wrapper: WrapperMinting):
    steth_to_rebalance = 10_000

    wrapper.vault_rebalance_minted_liability_steth("user1", steth_to_rebalance)
    assert wrapper.assets_of("user1") == approx(user1_initial_eth - steth_to_rebalance, TOLERANCE)
