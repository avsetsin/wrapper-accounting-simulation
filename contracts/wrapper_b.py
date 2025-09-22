from contracts.vault import Vault
from contracts.wrapper_minting import WrapperMinting


class WrapperB(WrapperMinting):
    def __init__(self, vault: Vault, reserve_ratio: float):
        super().__init__(vault, reserve_ratio)
