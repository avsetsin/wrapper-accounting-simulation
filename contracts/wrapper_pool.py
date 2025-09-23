from math import ceil, floor
from typing import Callable
from contracts.vault import Vault


class WrapperPool:
    def __init__(self, vault: Vault):
        self.vault = vault

        # eth pool
        self._total_shares: int = 0
        self._shares: dict[str, int] = {}

    # totals methods

    def get_total_value(self):
        return self.vault.get_total_value()

    def get_total_shares(self):
        return self._total_shares

    def get_total_effective_value(self):
        """excludes shared liability"""
        return self.get_total_value() - self.get_total_shared_liability_steth()

    # totals liability methods

    def get_total_vault_liability_wsteth(self):
        return self.vault.get_total_liability_shares()

    def get_total_vault_liability_steth(self):
        return self.vault.lido.get_pooled_eth_by_shares_rounded_up(self.get_total_vault_liability_wsteth())

    def get_total_shared_liability_wsteth(self):
        return self.get_total_vault_liability_wsteth()

    def get_total_shared_liability_steth(self):
        return self.vault.lido.get_pooled_eth_by_shares_rounded_up(self.get_total_shared_liability_wsteth())

    # user shared liability methods

    def shared_liability_wsteth(self, user: str):
        if self.get_total_shares() == 0:
            return 0

        return ceil(self.get_total_shared_liability_wsteth() * self.shares_of(user) / self.get_total_shares())

    def shared_liability_steth(self, user: str):
        return self.vault.lido.get_pooled_eth_by_shares_rounded_up(self.shared_liability_wsteth(user))

    # user assets methods

    def stake_eth(self, user: str, amount: int):
        self._check_positive_amount(amount)
        self._check_positive_shared_liability()

        shares = self.effective_assets_to_shares(amount)
        self._mint_shares(user, shares)
        self.vault.increase_total_value(amount)

    def withdraw_eth(self, user: str, amount: int):
        self._check_positive_amount(amount)
        self._check_positive_shared_liability()
        self._withdraw_eth(user, amount)

    def _withdraw_eth(self, user: str, amount: int):
        shares = self.effective_assets_to_shares(amount)
        if shares > self.shares_of(user):
            raise ValueError("Not enough shares to withdraw")
        self._burn_shares(user, shares)
        self.vault.decrease_total_value(amount)

    def assets_of(self, user: str):
        return self.shares_to_assets(self.balance_of(user))

    def effective_assets_of(self, user: str):
        return max(0, self.assets_of(user) - self.shared_liability_steth(user))

    # user shares methods

    def shares_of(self, user: str):
        return self._shares.get(user, 0)

    def balance_of(self, user: str):
        return self.shares_of(user)

    def _mint_shares(self, user: str, shares: int):
        self._shares[user] = self.shares_of(user) + shares
        self._total_shares += shares

    def _burn_shares(self, user: str, shares: int):
        if self.shares_of(user) < shares:
            raise ValueError("Not enough shares to burn")

        self._shares[user] -= shares
        self._total_shares -= shares

    # convert methods

    def assets_to_shares(self, assets: int, round: Callable[[float], int] = floor):
        if self.get_total_value() == 0:
            return assets
        return round(assets * self.get_total_shares() / self.get_total_value())

    def shares_to_assets(self, shares: int, round: Callable[[float], int] = floor):
        if self.get_total_shares() == 0:
            return 0
        return round(shares * self.get_total_value() / self.get_total_shares())

    def effective_assets_to_shares(self, assets: int, round: Callable[[float], int] = floor):
        """uses effective total value which excludes shared liability"""
        if self.get_total_effective_value() == 0:
            return assets
        return round(assets * self.get_total_shares() / self.get_total_effective_value())

    # shared liability methods

    def is_positive_shared_liability(self):
        return self.get_total_shared_liability_wsteth() > 0

    # rebalance methods

    def rebalance_total_shared_liability_wsteth(self, wsteth: int):
        if wsteth <= 0:
            raise ValueError("Rebalance amount must be positive")

        if wsteth > self.get_total_shared_liability_wsteth():
            raise ValueError("Cannot rebalance more than the shared liability")

        self.vault.rebalance(wsteth)

    def rebalance_total_shared_liability_steth(self, steth: int):
        wsteth = self.vault.lido.get_shares_by_pooled_eth_rounded_up(steth)
        self.rebalance_total_shared_liability_wsteth(wsteth)

    # checks

    def _check_positive_amount(self, amount: int):
        if amount <= 0:
            raise ValueError("Amount must be positive")

    def _check_positive_shared_liability(self):
        if self.is_positive_shared_liability():
            raise ValueError("Operation not allowed with positive shared liability")
