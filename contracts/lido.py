from math import ceil


class Lido:
    _share_rate = 1.2

    def get_pooled_eth_by_shares(self, shares: int):
        return int(shares * self._share_rate)

    def get_pooled_eth_by_shares_rounded_up(self, shares: int):
        return ceil(shares * self._share_rate)

    def get_shares_by_pooled_eth(self, eth: int):
        return int(eth // self._share_rate)

    def get_shares_by_pooled_eth_rounded_up(self, eth: int):
        return ceil(eth / self._share_rate)
