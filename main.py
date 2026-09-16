"""
اپلیکیشن نمایش قیمت ارز - نسخه اولیه
سه دسته: ارز بین‌المللی / ارز دیجیتال / بازار آزاد ایران (نمونه)
"""

import requests
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock


# ---------- توابع گرفتن داده از منابع مختلف ----------

def fetch_forex_rates():
    """قیمت ارزهای بین‌المللی نسبت به دلار (رایگان، بدون نیاز به API Key)"""
    try:
        resp = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=8)
        data = resp.json()
        rates = data.get("rates", {})
        wanted = ["EUR", "GBP", "TRY", "AED", "JPY", "CNY"]
        return [(code, rates[code]) for code in wanted if code in rates]
    except Exception as e:
        return [("خطا", str(e))]


def fetch_crypto_prices():
    """قیمت چند ارز دیجیتال (رایگان، از CoinGecko)"""
    try:
        ids = "bitcoin,ethereum,tether,binancecoin,ripple"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        resp = requests.get(url, timeout=8)
        data = resp.json()
        names = {
            "bitcoin": "بیت‌کوین",
            "ethereum": "اتریوم",
            "tether": "تتر",
            "binancecoin": "بایننس‌کوین",
            "ripple": "ریپل",
        }
        return [(names.get(k, k), v.get("usd")) for k, v in data.items()]
    except Exception as e:
        return [("خطا", str(e))]


def fetch_iran_market_rates():
    """
    نرخ بازار آزاد ایران (دلار/یورو/طلا).
    نکته مهم: هیچ API رسمی و همیشه رایگانی برای این داده وجود نداره.
    اینجا فعلاً داده نمونه (mock) گذاشته شده - باید بعداً با یک منبع
    واقعی (مثل یک سرویس پولی/اسکرپینگ سایت‌های معتبر) جایگزین بشه.
    """
    return [
        ("دلار (نمونه)", "—"),
        ("یورو (نمونه)", "—"),
        ("طلای ۱۸ عیار (نمونه)", "—"),
    ]


# ---------- ساخت UI هر تب ----------

class RateList(ScrollView):
    def __init__(self, fetch_func, unit_label="$", **kwargs):
        super().__init__(**kwargs)
        self.fetch_func = fetch_func
        self.unit_label = unit_label
        self.grid = GridLayout(cols=2, size_hint_y=None, spacing=8, padding=8)
        self.grid.bind(minimum_height=self.grid.setter("height"))
        self.add_widget(self.grid)
        self.refresh()

    def refresh(self):
        self.grid.clear_widgets()
        rates = self.fetch_func()
        for name, value in rates:
            self.grid.add_widget(Label(text=str(name), size_hint_y=None, height=40))
            display_value = f"{value} {self.unit_label}" if value != "—" else "—"
            self.grid.add_widget(Label(text=str(display_value), size_hint_y=None, height=40))


class RootLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        self.tabs = TabbedPanel(do_default_tab=False)

        self.forex_tab = TabbedPanelItem(text="بین‌المللی")
        self.forex_list = RateList(fetch_forex_rates, unit_label="(به ازای 1 دلار)")
        self.forex_tab.add_widget(self.forex_list)

        self.crypto_tab = TabbedPanelItem(text="کریپتو")
        self.crypto_list = RateList(fetch_crypto_prices, unit_label="$")
        self.crypto_tab.add_widget(self.crypto_list)

        self.iran_tab = TabbedPanelItem(text="بازار آزاد ایران")
        self.iran_list = RateList(fetch_iran_market_rates, unit_label="")
        self.iran_tab.add_widget(self.iran_list)

        self.tabs.add_widget(self.forex_tab)
        self.tabs.add_widget(self.crypto_tab)
        self.tabs.add_widget(self.iran_tab)

        self.add_widget(self.tabs)

        refresh_btn = Button(text="بروزرسانی قیمت‌ها", size_hint_y=None, height=50)
        refresh_btn.bind(on_press=self.refresh_all)
        self.add_widget(refresh_btn)

    def refresh_all(self, *args):
        self.forex_list.refresh()
        self.crypto_list.refresh()
        self.iran_list.refresh()


class CurrencyApp(App):
    def build(self):
        self.title = "قیمت ارز"
        root = RootLayout()
        # بروزرسانی خودکار هر 5 دقیقه
        Clock.schedule_interval(lambda dt: root.refresh_all(), 300)
        return root


if __name__ == "__main__":
    CurrencyApp().run()
