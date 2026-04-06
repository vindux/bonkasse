from dataclasses import dataclass, field


@dataclass
class CartItem:
    menu_item_id: int
    name: str
    price: float
    vat_rate: float
    print_bon: bool


class Cart:
    def __init__(self):
        self.items: list[CartItem] = []

    @property
    def total(self) -> float:
        return sum(item.price for item in self.items)

    @property
    def is_empty(self) -> bool:
        return len(self.items) == 0

    @property
    def count(self) -> int:
        return len(self.items)

    def add(self, item: CartItem):
        self.items.append(item)

    def remove_last(self) -> CartItem | None:
        if self.items:
            return self.items.pop()
        return None

    def clear(self):
        self.items.clear()


# Single global cart instance (kiosk = one user)
_cart = Cart()


def get_cart() -> Cart:
    return _cart
