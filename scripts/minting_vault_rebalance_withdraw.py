from contracts.lido import Lido
from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting
from scripts.utils.print_users_minting import print_users

wrapper = WrapperMinting(Vault(Lido(), liability_limit_steth=1_000_000, reserve_ratio=0.2), reserve_ratio=0.25)


def main():
    wrapper.stake_eth("user 1", 100_000)
    wrapper.stake_eth("user 2", 50_000)
    print_users(wrapper, "Initial state")

    wrapper.mint_steth("user 1", 50_000)
    wrapper.mint_steth("user 2", 20_000)
    print_users(wrapper, "Mint wstETH for users")

    wrapper.vault.rebalance(wrapper.vault.get_total_liability_shares())
    print_users(wrapper, "Vault rebalance total liability")

    wrapper.shared_rebalance_minted_liability_wsteth("user 1", wrapper.minted_liability_wsteth("user 1"))
    print_users(wrapper, "Internal rebalance")

    wrapper.withdraw_eth("user 1", wrapper.withdrawable_effective_assets_of("user 1"))
    print_users(wrapper, "User 1 withdraws all")


if __name__ == "__main__":
    main()
