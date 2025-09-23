from pytest import approx, fixture, raises
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting

TOLERANCE = 2  # due to rounding


@fixture(scope="function")
def wrapper():
    return WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)


def test_vault_extra_debt(wrapper: WrapperMinting):
    user1_initial_eth = 100_000
    user2_initial_eth = 200_000

    wrapper.stake_eth("user1", user1_initial_eth)
    wrapper.stake_eth("user2", user2_initial_eth)

    minted_steth = 70_000
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
    # transfer debt from another vault
    ##

    extra_debt_steth = 25_000
    extra_debt_wsteth = wrapper.vault.lido.get_shares_by_pooled_eth(extra_debt_steth)
    wrapper.vault.increase_liability(extra_debt_wsteth)

    # after extra debt is added, total liability increases
    assert wrapper.get_total_vault_liability_steth() == approx(minted_steth + extra_debt_steth, TOLERANCE)
    assert wrapper.get_total_minted_liability_steth() == approx(minted_steth, TOLERANCE)
    assert wrapper.get_total_shared_liability_steth() == approx(extra_debt_steth, TOLERANCE)

    # extra debt is distributed pro-rata to shares
    assert wrapper.shared_liability_steth("user1") == approx(extra_debt_steth * 1 / 3, TOLERANCE)
    assert wrapper.shared_liability_steth("user2") == approx(extra_debt_steth * 2 / 3, TOLERANCE)

    # all user operations are blocked until extra debt is rebalanced
    assert_user_operations_blocked(wrapper)

    ##
    # rebalance half of the extra debt
    ##

    wrapper.rebalance_total_shared_liability_wsteth(wrapper.get_total_shared_liability_wsteth() // 2)
    half_extra_debt_steth = extra_debt_steth // 2

    # half of the extra debt is rebalanced
    assert wrapper.get_total_vault_liability_steth() == approx(minted_steth + half_extra_debt_steth, TOLERANCE)
    assert wrapper.get_total_minted_liability_steth() == approx(minted_steth, TOLERANCE)
    assert wrapper.get_total_shared_liability_steth() == approx(half_extra_debt_steth, TOLERANCE)

    # remaining extra debt is still distributed pro-rata to shares
    assert wrapper.shared_liability_steth("user1") == approx(half_extra_debt_steth * 1 / 3, TOLERANCE)
    assert wrapper.shared_liability_steth("user2") == approx(half_extra_debt_steth * 2 / 3, TOLERANCE)

    # all user operations are blocked until extra debt is rebalanced
    assert_user_operations_blocked(wrapper)

    ##
    # rebalance the rest of the extra debt
    ##

    wrapper.rebalance_total_shared_liability_wsteth(wrapper.get_total_shared_liability_wsteth())

    # all extra debt is rebalanced
    assert wrapper.get_total_vault_liability_steth() == minted_steth
    assert wrapper.get_total_minted_liability_steth() == minted_steth
    assert wrapper.get_total_shared_liability_steth() == 0

    # total value is correctly calculated
    assert wrapper.get_total_value() == approx(user1_initial_eth + user2_initial_eth - extra_debt_steth, TOLERANCE)
    assert wrapper.get_total_shares() == user1_initial_eth + user2_initial_eth

    # liability is correctly assigned to users
    assert wrapper.shared_liability_steth("user1") == 0
    assert wrapper.shared_liability_steth("user2") == 0

    # user assets and balances are correctly adjusted for extra debt
    assert wrapper.assets_of("user1") == approx(user1_initial_eth - extra_debt_steth * 1 / 3, TOLERANCE)
    assert wrapper.balance_of("user1") == approx(user1_initial_eth, TOLERANCE)
    assert wrapper.assets_of("user2") == approx(user2_initial_eth - extra_debt_steth * 2 / 3, TOLERANCE)
    assert wrapper.balance_of("user2") == approx(user2_initial_eth, TOLERANCE)

    # user operations are allowed again
    balance_before = wrapper.assets_of("user1")
    wrapper.stake_eth("user1", 10_000)
    assert wrapper.assets_of("user1") == approx(balance_before + 10_000)


def assert_user_operations_blocked(wrapper: WrapperMinting):
    for operation in [
        lambda: wrapper.stake_eth("user1", 10),
        lambda: wrapper.withdraw_eth("user1", 10),
        lambda: wrapper.mint_steth("user1", 10),
        lambda: wrapper.burn_steth("user1", 10),
    ]:
        with raises(ValueError, match="Operation not allowed with positive shared liability"):
            operation()
