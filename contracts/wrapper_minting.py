from math import ceil, floor
from typing import Callable
from contracts.vault import Vault
from contracts.wrapper_pool import WrapperPool


class WrapperMinting(WrapperPool):
    def __init__(self, vault: Vault, reserve_ratio: float):
        super().__init__(vault)

        if vault.reserve_ratio > reserve_ratio:
            raise ValueError("Wrapper reserve ratio must be >= vault reserve ratio")

        self.reserve_ratio = reserve_ratio

        # debt pool. numbers can be negative
        self._total_minted_wsteth: int = 0
        self._minted_wsteth: dict[str, int] = {}

    # totals liability methods

    def get_total_minted_liability_wsteth(self):
        return self._total_minted_wsteth

    def get_total_minted_liability_steth(self):
        return self.vault.lido.get_pooled_eth_by_shares_rounded_up(self.get_total_minted_liability_wsteth())

    def get_total_shared_liability_wsteth(self):
        # overridden to account for minted liability
        return self.get_total_vault_liability_wsteth() - self.get_total_minted_liability_wsteth()

    # user liability methods

    def minted_liability_wsteth(self, user: str):
        return self._minted_wsteth.get(user, 0)

    def minted_liability_steth(self, user: str):
        return self.vault.lido.get_pooled_eth_by_shares_rounded_up(self.minted_liability_wsteth(user))

    def liability_wsteth_of(self, user: str):
        return self.shared_liability_wsteth(user) + self.minted_liability_wsteth(user)

    def liability_steth_of(self, user: str):
        return self.shared_liability_steth(user) + self.minted_liability_steth(user)

    # user assets methods

    def withdraw_eth(self, user: str, amount: int):
        # overridden to check withdrawable collateral
        self._check_positive_amount(amount)
        self._check_positive_shared_liability()

        if amount > self.withdrawable_effective_assets_of(user):
            raise ValueError("Not enough withdrawable assets to withdraw")

        self._withdraw_eth(user, amount)

    # minted liability

    def mint_steth(self, user: str, steth: int):
        wsteth = self.vault.lido.get_shares_by_pooled_eth(steth)
        self.mint_wsteth(user, wsteth)

    def mint_wsteth(self, user: str, wsteth: int):
        self._check_positive_amount(wsteth)
        self._check_positive_shared_liability()
        self._check_reserve_ratio(user, wsteth)

        self.vault.increase_liability(wsteth)
        self._increase_internal_liability_wsteth(user, wsteth)

    def _increase_internal_liability_wsteth(self, user: str, wsteth: int):
        self._minted_wsteth[user] = self.minted_liability_wsteth(user) + wsteth
        self._total_minted_wsteth += wsteth

    def _decrease_internal_liability_wsteth(self, user: str, wsteth: int):
        if user not in self._minted_wsteth:
            self._minted_wsteth[user] = 0

        self._minted_wsteth[user] -= wsteth
        self._total_minted_wsteth -= wsteth

    def burn_steth(self, user: str, steth: int):
        wsteth = self.vault.lido.get_shares_by_pooled_eth_rounded_up(steth)
        self.burn_wsteth(user, wsteth)

    def burn_wsteth(self, user: str, wsteth: int):
        self._check_positive_amount(wsteth)
        self._check_positive_shared_liability()

        if self.minted_liability_wsteth(user) < wsteth:
            raise ValueError("Not enough minted liability to burn")

        self._decrease_internal_liability_wsteth(user, wsteth)
        self.vault.decrease_liability(wsteth)

    # withdrawable

    def withdrawable_effective_assets_of(self, user: str):
        minted_liability = self.minted_liability_steth(user)
        shared_liability = self.shared_liability_steth(user)
        total_liability = minted_liability + max(shared_liability, 0)

        required_reserve = floor(total_liability / (1 - self.reserve_ratio))
        return self.effective_assets_of(user) - required_reserve

    # user rebalance methods against vault

    def vault_rebalance_minted_liability_wsteth(self, user: str, wsteth: int):
        self._check_positive_amount(wsteth)
        liability_wsteth = self.liability_wsteth_of(user)
        steth_to_rebalance = self.vault.lido.get_pooled_eth_by_shares_rounded_up(wsteth)

        if wsteth > liability_wsteth:
            raise ValueError("Cannot rebalance more than the total liability")

        shares = self.effective_assets_to_shares(steth_to_rebalance)
        self._burn_shares(user, shares)
        self._decrease_internal_liability_wsteth(user, wsteth)
        self.vault.rebalance(wsteth)

    def vault_rebalance_minted_liability_steth(self, user: str, steth: int):
        wsteth = self.vault.lido.get_shares_by_pooled_eth_rounded_up(steth)
        self.vault_rebalance_minted_liability_wsteth(user, wsteth)

    # user rebalance methods against shared liability

    def shared_rebalance_minted_liability_wsteth(self, user: str, wsteth: int):
        self._check_positive_amount(wsteth)
        minted_wsteth = self.minted_liability_wsteth(user)
        shared_liability_wsteth = -self.get_total_shared_liability_wsteth()

        if minted_wsteth < wsteth:
            raise ValueError("Not enough minted liability to rebalance")

        if shared_liability_wsteth < wsteth:
            raise ValueError("Not enough shared liability to rebalance")

        steth_to_rebalance = self.vault.lido.get_pooled_eth_by_shares(wsteth)
        shares = self.effective_assets_to_shares(steth_to_rebalance)
        self._burn_shares(user, shares)
        self._decrease_internal_liability_wsteth(user, wsteth)

    def shared_rebalance_minted_liability_steth(self, user: str, steth: int):
        wsteth = self.vault.lido.get_shares_by_pooled_eth_rounded_up(steth)
        self.shared_rebalance_minted_liability_wsteth(user, wsteth)

    # checks

    def _check_reserve_ratio(self, user: str, wsteth_to_mint: int):
        steth_to_mint = self.vault.lido.get_pooled_eth_by_shares(wsteth_to_mint)
        minted_wsteth_after = self.minted_liability_wsteth(user) + wsteth_to_mint
        reserve_assets_after = max(0, self.assets_of(user) - self.liability_steth_of(user) - steth_to_mint)
        reserve_wsteth_after = self.vault.lido.get_shares_by_pooled_eth(reserve_assets_after)

        if minted_wsteth_after == 0:
            return

        if reserve_wsteth_after == 0:
            raise ValueError("Reserve ratio limit exceeded")

        if reserve_wsteth_after / (minted_wsteth_after + reserve_wsteth_after) < self.reserve_ratio:
            raise ValueError("Reserve ratio limit exceeded")
