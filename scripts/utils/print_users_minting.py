from contracts.wrapper_minting import WrapperMinting
from scripts.utils.formatting import blue, gray, green
from scripts.utils.print import print_line, print_joined, print_title


def print_users(wrapper: WrapperMinting, title: str):
    print_title(title)

    print_line(127)
    print_joined(
        f"{'user':<10}",
        f"{'shares':>12}",
        f"{'assets':>12}",
        f"{'debt wst':>12}",
        blue(f"{'debt st':>12}"),
        f"{'minted wst':>12}",
        blue(f"{'minted st':>12}"),
        f"{'shared wst':>12}",
        blue(f"{'shared st':>12}"),
        green(f"{'assets-debt':>12}"),
    )
    print_line(127)

    total_shares = 0
    total_value = 0
    total_debt_wsteth = 0
    total_debt_steth = 0

    for user in wrapper._shares.keys():
        shares = wrapper.balance_of(user)
        assets = wrapper.assets_of(user)
        debt_wsteth = wrapper.liability_wsteth_of(user)
        debt_steth = wrapper.liability_steth_of(user)
        minted_wsteth = wrapper.minted_liability_wsteth(user)
        minted_steth = wrapper.minted_liability_steth(user)
        shared_wsteth = wrapper.shared_liability_wsteth(user)
        shared_steth = wrapper.shared_liability_steth(user)
        value = assets - debt_steth

        print_joined(
            gray(f"{user:<10}"),
            gray(f"{shares:>12,.0f}"),
            gray(f"{assets:>12,.0f}"),
            gray(f"{debt_wsteth:>12,.0f}"),
            gray(f"{debt_steth:>12,.0f}"),
            gray(f"{minted_wsteth:>12,.0f}"),
            gray(f"{minted_steth:>12,.0f}"),
            gray(f"{shared_wsteth:>12,.0f}"),
            gray(f"{shared_steth:>12,.0f}"),
            gray(f"{value:>12,.0f}"),
        )

        total_shares += shares
        total_value += assets
        total_debt_wsteth += debt_wsteth
        total_debt_steth += debt_steth

    print_line(127)
    print_joined(
        f"{'total sum':<10}",
        f"{total_shares:>12,.0f}",
        f"{total_value:>12,.0f}",
        f"{total_debt_wsteth:>12,.0f}",
        f"{total_debt_steth:>12,.0f}",
    )
    print_line(62)
    print_joined(
        f"{'in wrapper':<10}",
        gray(f"{wrapper.get_total_shares():>12,.0f}"),
        gray(f"{wrapper.get_total_value():>12,.0f}"),
        gray(f"{wrapper.get_total_minted_liability_wsteth():>12,.0f}"),
        gray(f"{wrapper.get_total_minted_liability_steth():>12,.0f}"),
    )
    print_joined(
        f"{'minted debt':<36}",
        gray(f"{wrapper.get_total_minted_liability_wsteth():>12,.0f}"),
        gray(f"{wrapper.get_total_minted_liability_steth():>12,.0f}"),
    )
    print_joined(
        f"{'shared debt':<36}",
        gray(f"{wrapper.get_total_shared_liability_wsteth():>12,.0f}"),
        gray(f"{wrapper.get_total_shared_liability_steth():>12,.0f}"),
    )
    print_joined(
        f"{'vault debt':<36}",
        gray(f"{wrapper.get_total_vault_liability_wsteth():>12,.0f}"),
        gray(f"{wrapper.get_total_vault_liability_steth():>12,.0f}"),
    )

    print_line(62)
    print()
