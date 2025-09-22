from pytest import approx, fixture, raises
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting

TOLERANCE = 2  # due to rounding


@fixture(scope="function")
def wrapper():
    return WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)


def test_vault_rebalance(wrapper: WrapperMinting):
    user1_initial_eth = 100_000
    user2_initial_eth = 200_000

    wrapper.stake_eth("user1", user1_initial_eth)
    wrapper.stake_eth("user2", user2_initial_eth)

    minted_steth = 60_000
    wrapper.mint_steth("user1", minted_steth)

    # total liability is correctly set after mint
    assert wrapper.get_total_vault_liability_steth() == minted_steth
    assert wrapper.get_total_minted_liability_steth() == minted_steth
    assert wrapper.get_total_shared_liability_steth() == 0

    # total value and shares are correct
    assert wrapper.get_total_value() == user1_initial_eth + user2_initial_eth
    assert wrapper.get_total_shares() == user1_initial_eth + user2_initial_eth

    # liability is correctly assigned to users
    assert wrapper.shared_liability_steth("user1") == 0
    assert wrapper.shared_liability_steth("user2") == 0
    assert wrapper.minted_liability_steth("user1") == minted_steth
    assert wrapper.minted_liability_steth("user2") == 0
    assert wrapper.liability_steth_of("user1") == minted_steth
    assert wrapper.liability_steth_of("user2") == 0

    ##
    # rebalance half of the minted liability
    ##

    rebalanced_wsteth = wrapper.vault.get_total_liability_shares() // 2
    rebalanced_steth = wrapper.vault.lido.get_pooled_eth_by_shares_rounded_up(rebalanced_wsteth)
    wrapper.vault.rebalance(rebalanced_wsteth)

    # minted liability remains the same
    assert wrapper.get_total_minted_liability_steth() == minted_steth

    # shared liability is now negative
    assert wrapper.get_total_shared_liability_steth() < 0
    assert wrapper.get_total_shared_liability_steth() == -rebalanced_steth

    # total liability decreases
    assert wrapper.get_total_vault_liability_steth() == rebalanced_steth

    # shared liability is distributed pro-rata to shares
    assert wrapper.shared_liability_steth("user1") == approx(-rebalanced_steth / 3, TOLERANCE)
    assert wrapper.shared_liability_steth("user2") == approx(-rebalanced_steth / 3 * 2, TOLERANCE)
