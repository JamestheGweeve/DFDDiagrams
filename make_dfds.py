#!/usr/bin/env python3
#install graphviz and https://pypi.org/project/data-flow-diagram/
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

FMT = sys.argv[1] if len(sys.argv) > 1 else "svg"
OUT = Path("dfd_output")

# Level 0: context diagram

LEVEL0 = """
entity    Customer
entity    Gateway   Payment gateway
entity    Store     Grocery store
entity    Driver    Delivery driver
process   System    0. Grocery delivery system

Customer --> System   Orders, account info
System   --> Customer Status updates
Gateway  --> System   Auth result
System   --> Gateway  Payment request
System   --> Store    Order details
Store    --> System   Catalogue, stock
System   --> Driver   Delivery job
Driver   --> System   Location, status
"""

# Level 1

LEVEL1 = """
entity    Customer
entity    Store     Grocery store
entity    Gateway   Payment gateway
entity    Driver    Delivery driver

process   P1   1. Manage accounts
process   P2   2. Browse catalogue
process   P3   3. Manage cart
process   P4   4. Process payment
process   P5   5. Manage orders
process   P6   6. Dispatch driver

store     D1   Accounts
store     D2   Catalogue
store     D3   Orders, payments

Customer --> P1   Account details
P1 --> Customer   Confirmation
Customer --> P2   Search, address
P2 --> Customer   Search results
Customer --> P3   Cart edits, tip
P3 --> Customer   Order total
Customer --> P4   Payment choice
P4 --> Customer   Receipt
Customer --> P5   Order changes
P5 --> Customer   Status updates

P1 --> D1   Account data
D1 --> P1   Saved details
P2 --> D2   Search query
D2 --> P2   Products, stock
Store --> D2   Catalogue feed
D2 --> P3   Prices, stock

P2 --> P3   Selected items
P3 --> P4   Checkout order
P4 --> Gateway   Charge, refund
Gateway --> P4   Auth result
P4 --> P5   Paid order
P5 --> P4   Refund request

P5 --> Store   Order details
Store --> P5   Stock, substitutes
P5 --> D3   Order record
D3 --> P5   Delivery status
D3 --> P6   Orders to dispatch
P6 --> D3   Delivery status
Driver --> P6   Driver status
P6 --> Driver   Delivery job
"""

# Level 2: 5.0 Manage orders

LEVEL2_ORDERS = """
entity    Customer
entity    Store     Grocery store
store     D3        Orders
process   P40       4. Process payment (Level 1)
process   P51       5-1 Track order
process   P52       5-2 Modify order
process   P53       5-3 Cancel order

Customer --> P51   Order lookup
P51 --> Customer   Status, alerts
Customer --> P52   Order changes
P52 --> Customer   Updated order
Customer --> P53   Cancel request
P53 --> Customer   Cancel receipt

D3 --> P51   Order status
P52 --> D3   Updated order
P53 --> D3   Cancelled order
D3 --> P53   Order record

P52 --> Store   Order details
Store --> P52   Substitutes

P53 --> P40   Refund request
"""

# Level 2: 3.0 Manage cart

LEVEL2_CART = """
entity    Customer
store     D2        Catalogue
process   P20       2. Browse catalogue (Level 1)
process   P40       4. Process payment (Level 1)
process   P31       3-1 Update cart
process   P32       3-2 Apply promotions
process   P33       3-3 Calculate total

P20 --> P31   Selected items
P31 --> P32   Cart items
P32 --> P33   Discounted cart
P33 --> P40   Checkout order

Customer --> P31   Item edits
P31 --> Customer   Cart contents
Customer --> P32   Promo code
P32 --> Customer   Discounts shown
Customer --> P33   Tip amount
P33 --> Customer   Order total

D2 --> P31   Prices, stock
D2 --> P32   Promo rules
"""

DIAGRAMS = {
    "level0_context": LEVEL0,
    "level1": LEVEL1,
    "level2_manage_orders": LEVEL2_ORDERS,
    "level2_manage_cart": LEVEL2_CART,
}



RUNNER = "import sys; from data_flow_diagram import main; sys.argv[0] = 'data-flow-diagram'; sys.exit(main())"


def render(name: str, source: str) -> None:
    dfd_file = OUT / f"{name}.dfd"
    out_file = OUT / f"{name}.{FMT}"
    dfd_file.write_text(source.strip() + "\n", encoding="utf-8")
    subprocess.run(
        [sys.executable, "-c", RUNNER, str(dfd_file), "-o", str(out_file),
         "--format", FMT, "--no-graph-title"],
        check=True,
    )
    print(f"wrote {out_file}")


def find_graphviz() -> bool:
    """Make sure `dot` is reachable; on Windows, search the usual install folders."""
    if shutil.which("dot"):
        return True
    patterns = [
        r"C:\Program Files\Graphviz*\bin",
        r"C:\Program Files (x86)\Graphviz*\bin",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Graphviz*\bin"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Graphviz*\**\bin"),
    ]
    for pattern in patterns:
        for folder in glob.glob(pattern, recursive=True):
            if os.path.exists(os.path.join(folder, "dot.exe")):
                os.environ["PATH"] = folder + os.pathsep + os.environ["PATH"]
                print(f"using Graphviz from {folder}")
                return True
    return False


if __name__ == "__main__":
    if not find_graphviz():
        sys.exit("Graphviz (dot) not found. Install it from https://graphviz.org/download/ "
                 "or run `winget install Graphviz.Graphviz`, then re-run this script.")
    OUT.mkdir(exist_ok=True)
    for name, source in DIAGRAMS.items():
        render(name, source)
