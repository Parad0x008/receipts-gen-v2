import random
from collections import Counter
from typing import Dict, List, Tuple
import streamlit as st
import pandas as pd
import altair as alt

class ReceiptGenerator:
    def __init__(self, items_prices: Dict[str, float]):
        self.items_prices = items_prices

    def generate_receipts(self, total_amount: float, total_receipts: int) -> Tuple[List[List[Tuple[str, int, float]]], float]:
        items = list(self.items_prices.keys())
        receipts = [[] for _ in range(total_receipts)]
        total_all = 0

        # Generate random target amounts for each receipt that sum up to the total_amount
        receipt_targets = [random.uniform(0.8, 1.2) for _ in range(total_receipts)]
        sum_targets = sum(receipt_targets)
        receipt_targets = [(total_amount * target) / sum_targets for target in receipt_targets]

        # Try to allocate items to each receipt based on the generated target amounts
        for i in range(total_receipts):
            current_total = 0
            while current_total < receipt_targets[i]:
                remaining_amount = receipt_targets[i] - current_total
                available_items = [item for item in items if self.items_prices[item] <= remaining_amount]

                if not available_items:
                    break

                item = random.choice(available_items)
                max_qty = int(remaining_amount // self.items_prices[item])

                if max_qty > 0:
                    qty = random.randint(1, max_qty)
                    receipts[i].append((item, qty, self.items_prices[item]))
                    current_total += qty * self.items_prices[item]

            total_all += current_total

        return receipts, total_all

def main():
    st.title("Receipt Generator V2 🤞")

    if "items_prices" not in st.session_state:
        st.session_state.items_prices = {}

    with st.container():
        st.subheader("Items and Prices")

        # Check if the form is being submitted
        with st.form(key='items_prices_form', clear_on_submit=False):
            item_name = st.text_input('Item name')
            item_price = st.number_input('Item price', min_value=1, step=1)
            submitted = st.form_submit_button('Add Item')

            # If form is submitted, add the new item to session state
            if submitted and item_name:
                st.session_state.items_prices[item_name] = item_price

        # Convert the session state items and prices to a DataFrame
        df = pd.DataFrame([(item, price) for item, price in st.session_state.items_prices.items()],
                            columns=["Item", "Price"])

        # Display the current items and prices
        st.dataframe(df)

    total_amount = st.number_input('Total target amount (Rs)', min_value=1, step=1)
    total_receipts = st.number_input('Number of receipts', min_value=1, step=1)

    if st.button('Generate Receipts'):
        if not st.session_state.items_prices:
            st.error("Please add some items before generating receipts.")
        else:
            generator = ReceiptGenerator(st.session_state.items_prices)
            with st.spinner("Generating receipts..."):
                receipts, total_all = generator.generate_receipts(total_amount, total_receipts)

            st.success(f"Generated {len(receipts)} receipts with a total of Rs {int(total_all)}")

            for i, receipt in enumerate(receipts, 1):
                with st.expander(f"Receipt {i}"):
                    df = pd.DataFrame(receipt, columns=["Item", "Quantity", "Price"])
                    df["Total"] = df["Price"] * df["Quantity"]
                    df = df[["Item", "Quantity", "Price", "Total"]]
                    st.dataframe(df)
                    st.write(f"Receipt Total: Rs {int(df['Total'].sum())}")

            # Visualization
            all_items = Counter()
            for receipt in receipts:
                all_items.update(dict([(item, qty) for item, qty, _ in receipt]))

            chart_data = pd.DataFrame.from_dict(all_items, orient='index', columns=['Quantity']).reset_index()
            chart_data.columns = ['Item', 'Quantity']

            chart = alt.Chart(chart_data).mark_bar().encode(
                x='Item',
                y='Quantity',
                color='Item'
            ).properties(
                title='Total Quantity of Items Across All Receipts'
            )

            st.altair_chart(chart, use_container_width=True)

if __name__ == "__main__":
    main()
