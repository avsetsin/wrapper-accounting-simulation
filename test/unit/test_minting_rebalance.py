from pytest import fixture, approx
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting

TOLERANCE = 2  # due to rounding

user1_initial_eth = 100_000
user2_initial_eth = 200_000

user1_minted_steth = 50_000
user2_minted_steth = 50_000

total_initial_eth = user1_initial_eth + user2_initial_eth
total_minted_steth = user1_minted_steth + user2_minted_steth


@fixture(scope="function")
def wrapper():
    wrapper = WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)
    wrapper.stake_eth("user1", user1_initial_eth)
    wrapper.stake_eth("user2", user2_initial_eth)
    wrapper.mint_steth("user1", user1_minted_steth)
    wrapper.mint_steth("user2", user2_minted_steth)

    # all debt is rebalanced to assets
    wrapper.vault.rebalance(wrapper.vault.get_total_liability_shares())

    return wrapper


def test_initial_state(wrapper: WrapperMinting):
    assert wrapper.get_total_value() == approx(total_initial_eth - total_minted_steth, TOLERANCE)
    assert wrapper.get_total_shares() == user1_initial_eth + user2_initial_eth

    new_total_value = wrapper.get_total_value()

    # balances are proportional to initial assets
    assert wrapper.assets_of("user1") == approx(new_total_value * user1_initial_eth / total_initial_eth, TOLERANCE)
    assert wrapper.assets_of("user2") == approx(new_total_value * user2_initial_eth / total_initial_eth, TOLERANCE)

    # minted liabilities are not changed
    assert wrapper.minted_liability_steth("user1") == user1_minted_steth
    assert wrapper.minted_liability_steth("user2") == user2_minted_steth

    assert wrapper.get_total_shared_liability_steth() == approx(-(user1_minted_steth + user2_minted_steth), TOLERANCE)
    assert wrapper.vault.get_total_liability_shares() == 0


def test_rebalance_to_assets_decrease_collateral(wrapper: WrapperMinting):
    assets_to_rebalance = 10_000

    assets_before = wrapper.collateral("user1")
    wrapper.rebalance_minted_liability_to_assets_steth("user1", assets_to_rebalance)
    assets_after = wrapper.collateral("user1")

    assert assets_before - assets_after == assets_to_rebalance
