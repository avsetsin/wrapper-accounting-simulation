from pytest import fixture, raises
from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting

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


def test_withdraw_less_than_collateral(wrapper: WrapperMinting):
    wrapper.withdraw_eth("user1", 100)


def test_withdraw_withdrawable_collateral(wrapper: WrapperMinting):
    assert wrapper.assets_of("user1") == user1_initial_eth
    assert wrapper.withdrawable_collateral("user1") > 0

    wrapper.withdraw_eth("user1", wrapper.withdrawable_collateral("user1"))

    assert wrapper.assets_of("user1") == user1_minted_steth // 0.75  # 25% reserve
    assert wrapper.withdrawable_collateral("user1") == 0


def test_revert_on_withdraw_more_than_collateral(wrapper: WrapperMinting):
    withdrawable_collateral = wrapper.withdrawable_collateral("user1")
    assert withdrawable_collateral > 0

    with raises(ValueError, match="Not enough withdrawable collateral"):
        wrapper.withdraw_eth("user1", withdrawable_collateral + 1)


def test_can_withdraw_all_after_debt_settled(wrapper: WrapperMinting):
    wrapper.burn_wsteth("user1", wrapper.minted_liability_wsteth("user1"))
    wrapper.withdraw_eth("user1", user1_initial_eth)

    assert wrapper.assets_of("user1") == 0
