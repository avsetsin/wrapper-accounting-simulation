from pytest import fixture, raises
from math import floor
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting

user1_initial_eth = 100_000
user2_initial_eth = 100_000


@fixture(scope="function")
def wrapper():
    wrapper = WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)
    wrapper.stake_eth("user1", user1_initial_eth)
    wrapper.stake_eth("user2", user2_initial_eth)
    return wrapper


def test_mint_increase_total_liability_on_vault(wrapper: WrapperMinting):
    wsteth_to_mint = 1000
    wrapper.mint_wsteth("user1", wsteth_to_mint)

    assert wrapper.vault.get_total_liability_shares() == wsteth_to_mint


def test_mint_does_not_change_total_value_or_shares(wrapper: WrapperMinting):
    total_value_before = wrapper.get_total_value()
    total_shares_before = wrapper.get_total_shares()

    wrapper.mint_wsteth("user1", 1000)

    assert wrapper.get_total_value() == total_value_before
    assert wrapper.get_total_shares() == total_shares_before


def test_revert_on_mint_zero(wrapper: WrapperMinting):
    with raises(Exception):
        wrapper.mint_wsteth("user1", 0)


def test_revert_on_mint_negative(wrapper: WrapperMinting):
    with raises(Exception):
        wrapper.mint_wsteth("user1", -1)


def test_revert_on_mint_over_reserve(wrapper: WrapperMinting):
    balance_in_steth = wrapper.assets_of("user1")
    balance_in_wsteth = wrapper.vault.lido.get_shares_by_pooled_eth(balance_in_steth)
    max_mintable_wsteth = floor(balance_in_wsteth * (1 - 0.25))
    wrapper.mint_wsteth("user1", max_mintable_wsteth)  # hit the limit

    with raises(Exception):
        wrapper.mint_wsteth("user1", 1)  # 1 more share


def test_revert_on_mint_more_than_vault_limit(wrapper: WrapperMinting):
    limit = wrapper.vault.liability_limit_steth

    wrapper.stake_eth("user1", 1_000_000_000)
    wrapper.mint_steth("user1", limit)  # hit the limit

    with raises(Exception):
        wrapper.mint_wsteth("user1", 1)  # 1 more share
