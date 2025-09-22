from contracts.vault import Vault
from contracts.wrapper_pool import WrapperPool


# TODO: add ERC-20 implementation to support transferability
class WrapperA(WrapperPool):
    def __init__(self, vault: Vault):
        super().__init__(vault)
