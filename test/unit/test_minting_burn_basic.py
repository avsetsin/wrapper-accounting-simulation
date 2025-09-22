from pytest import fixture, raises
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting

user1_initial_eth = 100_000
user2_initial_eth = 100_000
user1_minted_steth = 70_000
user2_minted_steth = 50_000


@fixture(scope="function")
def wrapper():
    wrapper = WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)
    wrapper.stake_eth("user1", user1_initial_eth)
    wrapper.stake_eth("user2", user2_initial_eth)
    wrapper.mint_steth("user1", user1_minted_steth)
    wrapper.mint_steth("user2", user2_minted_steth)
    return wrapper


def test_burn_decrease_total_liability_on_vault(wrapper: WrapperMinting):
    wsteth_to_burn = 1000
    total_liability_before = wrapper.vault.get_total_liability_shares()
    wrapper.burn_wsteth("user1", wsteth_to_burn)
    total_liability_after = wrapper.vault.get_total_liability_shares()

    assert total_liability_after == total_liability_before - wsteth_to_burn


def test_burn_does_not_change_total_value_or_shares(wrapper: WrapperMinting):
    total_value_before = wrapper.get_total_value()
    total_shares_before = wrapper.get_total_shares()

    wrapper.burn_wsteth("user1", 1000)

    assert wrapper.get_total_value() == total_value_before
    assert wrapper.get_total_shares() == total_shares_before


def test_revert_on_burn_zero(wrapper: WrapperMinting):
    with raises(Exception):
        wrapper.burn_wsteth("user1", 0)


def test_revert_on_burn_negative(wrapper: WrapperMinting):
    with raises(Exception):
        wrapper.burn_wsteth("user1", -1)


def test_revert_on_burn_over_user_debt(wrapper: WrapperMinting):
    liability_wsteth = wrapper.liability_wsteth_of("user1")
    wrapper.burn_wsteth("user1", liability_wsteth)  # pay off all debt

    with raises(Exception):
        wrapper.burn_wsteth("user1", 1)  # 1 more share
