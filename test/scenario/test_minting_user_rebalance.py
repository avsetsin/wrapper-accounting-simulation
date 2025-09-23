from pytest import approx, fixture, raises
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting

TOLERANCE = 2  # due to rounding


@fixture(scope="function")
def wrapper():
    return WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)


def test_user_rebalance(wrapper: WrapperMinting):
    user1_initial_eth = 100_000
    user2_initial_eth = 200_000

    wrapper.stake_eth("user1", user1_initial_eth)
    wrapper.stake_eth("user2", user2_initial_eth)

    user1_minted_steth = 60_000
    user2_minted_steth = 50_000

    wrapper.mint_steth("user1", user1_minted_steth)
    wrapper.mint_steth("user2", user2_minted_steth)

    # total liability is correctly set after mint
    assert wrapper.get_total_vault_liability_steth() == user1_minted_steth + user2_minted_steth
    assert wrapper.get_total_minted_liability_steth() == user1_minted_steth + user2_minted_steth
    assert wrapper.get_total_shared_liability_steth() == 0

    # total value and shares are correct
    assert wrapper.get_total_value() == user1_initial_eth + user2_initial_eth
    assert wrapper.get_total_shares() == user1_initial_eth + user2_initial_eth

    # liability is correctly assigned to users
    assert wrapper.shared_liability_steth("user1") == 0
    assert wrapper.shared_liability_steth("user2") == 0
    assert wrapper.minted_liability_steth("user1") == user1_minted_steth
    assert wrapper.minted_liability_steth("user2") == user2_minted_steth
    assert wrapper.liability_steth_of("user1") == user1_minted_steth
    assert wrapper.liability_steth_of("user2") == user2_minted_steth

    # rebalance partial user 1 debt
    wrapper.vault_rebalance_minted_liability_steth("user1", user1_minted_steth // 2)
    assert wrapper.minted_liability_steth("user1") == user1_minted_steth // 2

    # rebalance of user 1 do not affect user 2
    assert wrapper.liability_steth_of("user2") == user2_minted_steth
    assert wrapper.assets_of("user2") == user2_initial_eth

    # rebalance remaining user 1 debt
    wrapper.vault_rebalance_minted_liability_wsteth("user1", wrapper.liability_wsteth_of("user1"))
    assert wrapper.minted_liability_steth("user1") == 0
    assert wrapper.liability_steth_of("user1") == 0

    # total liability is correctly updated
    assert wrapper.get_total_vault_liability_steth() == user2_minted_steth
    assert wrapper.get_total_minted_liability_steth() == user2_minted_steth

    # rebalance user 2 debt fully
    wrapper.vault_rebalance_minted_liability_wsteth("user2", wrapper.liability_wsteth_of("user2"))
    assert wrapper.minted_liability_steth("user2") == 0
    assert wrapper.liability_steth_of("user2") == 0

    # total liability is correctly updated
    assert wrapper.get_total_vault_liability_steth() == 0
    assert wrapper.get_total_minted_liability_steth() == 0
    assert wrapper.get_total_shared_liability_steth() == 0

    # total value are correct
    assert wrapper.get_total_value() == user1_initial_eth + user2_initial_eth - user1_minted_steth - user2_minted_steth

    # users assets are correct
    assert wrapper.assets_of("user1") == user1_initial_eth - user1_minted_steth
    assert wrapper.assets_of("user2") == user2_initial_eth - user2_minted_steth
