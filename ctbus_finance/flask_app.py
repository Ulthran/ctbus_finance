from flask import Flask, render_template
from ctbus_finance.views import (
    get_accounts,
    get_credit_cards,
    get_net_value,
    get_monthly_net_worth,
    get_monthly_cash,
    get_monthly_credit_card_totals,
)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        net = get_net_value()
        net_trend = get_monthly_net_worth()
        cash_trend = get_monthly_cash()
        cc_trend = get_monthly_credit_card_totals()

        net_dict = dict(net_trend)
        cash_dict = dict(cash_trend)
        cc_dict = dict(cc_trend)
        labels = sorted(set(net_dict) | set(cash_dict) | set(cc_dict))

        net_values = [net_dict.get(m, 0) for m in labels]
        cash_values = [cash_dict.get(m, 0) for m in labels]
        cc_values = [cc_dict.get(m, 0) for m in labels]

        return render_template(
            "index.html",
            net_value=net,
            labels=labels,
            net_values=net_values,
            cash_values=cash_values,
            cc_values=cc_values,
        )

    @app.route("/accounts")
    def accounts():
        return render_template("accounts.html", accounts=get_accounts())

    @app.route("/credit_cards")
    def credit_cards():
        return render_template("credit_cards.html", credit_cards=get_credit_cards())

    return app


def main() -> None:
    app = create_app()
    app.run(debug=True, host="0.0.0.0")


if __name__ == "__main__":
    main()
