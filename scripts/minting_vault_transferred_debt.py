from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting
from scripts.utils.print_users_minting import print_users

wrapper = WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)


def main():
    wrapper.stake_eth("user 1", 100000)
    wrapper.stake_eth("user 2", 50000)
    wrapper.stake_eth("user 3", 30000)
    wrapper.stake_eth("user 4", 20000)
    print_users(wrapper, "Initial state")

    wrapper.vault.increase_total_value(20000)
    print_users(wrapper, "Total vault value increased due to staking rewards")

    wrapper.vault.increase_liability_steth(20000)
    print_users(wrapper, "Total liability increased due to transferred debt")

    # TODO: should we block operations until the rebalancing is done
    # wrapper.stake_eth("user 5", 20000)
    # print_users(wrapper, "User 5 stakes 20,000")

    wrapper.rebalance_total_shared_liability_wsteth(wrapper.get_total_shared_liability_wsteth() // 2)
    print_users(wrapper, "Half of the transferred debt rebalanced")

    wrapper.rebalance_total_shared_liability_wsteth(wrapper.get_total_shared_liability_wsteth())
    print_users(wrapper, "Whole transferred debt rebalanced")


if __name__ == "__main__":
    main()
