from typing import List
from app.models.offer import Offer

class InMemoryOfferStore:
    def __init__(self):
        self._offers: List[Offer] = []

    def add(self, offers: List[Offer]):
        self._offers.extend(offers)

    def get_all(self) -> List[Offer]:
        return self._offers

    def clear(self):
        self._offers = []


# 🔑 SINGLETON STORE (shared across the app)
offer_store = InMemoryOfferStore()
