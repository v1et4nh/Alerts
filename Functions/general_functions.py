def price_triggered(current_price, price_limit):
    bool_trigger = False
    if current_price <= price_limit:
        bool_trigger = True
    return bool_trigger
