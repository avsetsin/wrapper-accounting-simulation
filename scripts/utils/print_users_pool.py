from contracts.wrapper_pool import WrapperPool
from scripts.utils.formatting import blue, gray, green
from scripts.utils.print import print_line, print_joined, print_title


def print_users(wrapper: WrapperPool, title: str):
    print_title(title)

    print_line(75)
    print_joined(
        f"{'user':<10}",
        f"{'shares':>12}",
        f"{'assets':>12}",
        f"{'shared wst':>12}",
        blue(f"{'shared st':>12}"),
        green(f"{'assets-debt':>12}"),
    )
    print_line(75)

    total_shares = 0
    total_value = 0
    total_shared_wsteth = 0
    total_shared_steth = 0

    for user in wrapper._shares.keys():
        shares = wrapper.balance_of(user)
        assets = wrapper.assets_of(user)
        shared_wsteth = wrapper.shared_liability_wsteth(user)
        shared_steth = wrapper.shared_liability_steth(user)
        value = assets - shared_steth

        print_joined(
            gray(f"{user:<10}"),
            gray(f"{shares:>12,.0f}"),
            gray(f"{assets:>12,.0f}"),
            gray(f"{shared_wsteth:>12,.0f}"),
            gray(f"{shared_steth:>12,.0f}"),
            gray(f"{value:>12,.0f}"),
        )

        total_shares += shares
        total_value += assets

        total_shared_wsteth += shared_wsteth
        total_shared_steth += shared_steth

    print_line(75)
    print_joined(
        f"{'total sum':<10}",
        f"{total_shares:>12,.0f}",
        f"{total_value:>12,.0f}",
        f"{total_shared_wsteth:>12,.0f}",
        f"{total_shared_steth:>12,.0f}",
    )
    print_line(62)
    print_joined(
        f"{'in wrapper':<10}",
        gray(f"{wrapper.get_total_shares():>12,.0f}"),
        gray(f"{wrapper.get_total_value():>12,.0f}"),
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
