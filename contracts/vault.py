from contracts.lido import Lido


class Vault:
    def __init__(self, lido: Lido, liability_limit_steth: int, reserve_ratio: float):
        self.lido = lido
        self.liability_limit_steth = liability_limit_steth
        self.reserve_ratio = reserve_ratio

        self._total_value: int = 0
        self._liability_shares: int = 0

    # totals methods

    def get_total_value(self):
        return self._total_value

    def get_total_liability_shares(self):
        return self._liability_shares

    # liability methods

    def increase_liability(self, shares: int):
        if shares <= 0:
            raise ValueError("Shares must be positive")
        total_liability_shares_after = self.get_total_liability_shares() + shares
        total_liability_steth_after = self.lido.get_pooled_eth_by_shares_rounded_up(total_liability_shares_after)
        self._check_liability_limit(total_liability_steth_after)
        self._check_reserve_ratio(total_liability_steth_after)

        self._liability_shares += shares

    def increase_liability_steth(self, steth: int):
        shares = self.lido.get_shares_by_pooled_eth(steth)
        self.increase_liability(shares)

    def decrease_liability(self, shares: int):
        if shares <= 0:
            raise ValueError("Shares must be positive")
        if self._liability_shares < shares:
            raise ValueError("Not enough liability shares to decrease")
        self._liability_shares -= shares

    # total value methods

    def increase_total_value(self, eth: int):
        self._total_value += eth

    def decrease_total_value(self, eth: int):
        if self._total_value < eth:
            raise ValueError("Not enough total value to decrease")
        self._total_value -= eth

    # rebalance

    def rebalance(self, shares: int):
        eth = self.lido.get_pooled_eth_by_shares_rounded_up(shares)

        self.decrease_liability(shares)
        self.decrease_total_value(eth)

    # limits

    def _check_liability_limit(self, total_liability_steth: int):
        if total_liability_steth > self.liability_limit_steth:
            raise ValueError("Liability limit exceeded")

    def _check_reserve_ratio(self, total_liability_steth: int):
        reserve = self.get_total_value() - total_liability_steth

        if total_liability_steth == 0:
            return

        if self.get_total_value() == 0:
            raise ValueError("Reserve ratio limit exceeded")

        if reserve / self.get_total_value() < self.reserve_ratio:
            raise ValueError("Reserve ratio limit exceeded")
