from sqlalchemy import (
    Column,
    String,
    Float,
    ForeignKey,
    UniqueConstraint,
    Date,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    name = Column(
        String, nullable=False, primary_key=True
    )  # e.g., "My Brokerage Account"
    type = Column(String, nullable=False)  # e.g., brokerage, roth_ira, 403b
    institution = Column(String, nullable=True)  # e.g., Vanguard, Fidelity, Coinbase

    holdings = relationship("AccountHolding", back_populates="account")


class Holding(Base):
    __tablename__ = "holdings"

    symbol = Column(String, nullable=False, primary_key=True)  # e.g., AAPL, BTC
    name = Column(String, nullable=True)
    asset_type = Column(String, nullable=False)  # e.g., Stock, ETF, Crypto, Cash

    account_holdings = relationship("AccountHolding", back_populates="holding")


class AccountHolding(Base):
    __tablename__ = "account_holdings"
    __table_args__ = (
        UniqueConstraint(
            "account_id",
            "holding_id",
            "date",
            "purchase_date",
            name="uix_account_holding_date",
        ),
    )

    account_id = Column(
        String, ForeignKey("accounts.name"), primary_key=True, nullable=False
    )
    holding_id = Column(
        String, ForeignKey("holdings.symbol"), primary_key=True, nullable=False
    )
    date = Column(Date, primary_key=True, nullable=False)
    purchase_date = Column(Date, primary_key=True, nullable=True)

    quantity = Column(Float, nullable=False)  # Number of shares/units
    price = Column(Float, nullable=False)  # Price per share/unit
    purchase_price = Column(
        Float, nullable=True
    )  # Price at which the asset was purchased

    # Optional fields
    percentage_cash = Column(Float, nullable=True)  # Percentage of cash in the holding
    percentage_bond = Column(Float, nullable=True)  # Percentage of bond in the holding
    percentage_large_cap = Column(
        Float, nullable=True
    )  # Percentage of large cap stock in the holding
    percentage_mid_cap = Column(
        Float, nullable=True
    )  # Percentage of mid cap stock in the holding
    percentage_small_cap = Column(
        Float, nullable=True
    )  # Percentage of small cap stock in the holding
    percentage_international = Column(
        Float, nullable=True
    )  # Percentage of international stock in the holding
    percentage_other = Column(
        Float, nullable=True
    )  # Percentage of other assets in the holding

    notes = Column(String, nullable=True)  # Notes about the holding

    account = relationship("Account", back_populates="holdings")
    holding = relationship("Holding", back_populates="account_holdings")

    @property
    def total_value(self):
        return self.quantity * self.price

    @property
    def gain_loss(self):
        if self.purchase_price:
            return (self.price - self.purchase_price) * self.quantity
        return None


class CreditCard(Base):
    __tablename__ = "credit_cards"

    name = Column(String, nullable=False, primary_key=True)  # e.g., "Chase Sapphire"
    institution = Column(String, nullable=True)  # e.g., Chase, American Express
    card_type = Column(String, nullable=False)  # e.g., Visa, Mastercard

    holdings = relationship("CreditCardHolding", back_populates="credit_card")


class CreditCardHolding(Base):
    __tablename__ = "credit_card_holdings"

    credit_card_id = Column(
        String, ForeignKey("credit_cards.name"), primary_key=True, nullable=False
    )
    date = Column(Date, primary_key=True, nullable=False)
    balance = Column(Float, nullable=False)  # Current balance
    rewards = Column(Float, nullable=True)  # Current rewards balance

    credit_card = relationship("CreditCard", back_populates="holdings")

    @property
    def total_value(self):
        return (self.rewards if self.rewards else 0) - self.balance


class PriceCache(Base):
    """Persisted price data fetched from Yahoo Finance."""

    __tablename__ = "price_cache"

    symbol = Column(String, primary_key=True, nullable=False)
    date = Column(Date, primary_key=True, nullable=False)
    price = Column(Float, nullable=False)
