from flask import Flask, render_template
from ctbus_finance.views import (
    get_accounts,
    get_credit_cards,
    get_net_value,
    get_monthly_summary,
)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        net = get_net_value()
        trend = get_monthly_summary()
        return render_template("index.html", net_value=net, summary=trend)

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
