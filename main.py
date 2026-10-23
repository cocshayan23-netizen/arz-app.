import threading

import requests
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

try:  # نمایش درست فارسی (اختیاری)
    import arabic_reshaper
    from bidi.algorithm import get_display

    def fa(text):
        return get_display(arabic_reshaper.reshape(text))
except Exception:
    def fa(text):
        return text

# اگه فونت فارسی (مثلا Vazirmatn) کنار main.py گذاشتی، اینجا اسمش رو بذار
FONT = "Vazirmatn-Regular.ttf"
try:
    open(FONT).close()
except Exception:
    FONT = "Roboto"

Window.clearcolor = (0.07, 0.08, 0.11, 1)
TIMEOUT = 12


# ---------------------------------------------------------------- داده‌ها
def fetch_fiat():
    """نرخ ارزهای جهانی نسبت به دلار"""
    r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=TIMEOUT)
    rates = r.json()["rates"]
    names = {"EUR": "یورو", "GBP": "پوند", "AED": "درهم امارات",
             "TRY": "لیر ترکیه", "JPY": "ین ژاپن", "CAD": "دلار کانادا"}
    # قیمت هر واحد ارز به دلار
    return [(fa(n), f"${1 / rates[c]:,.4f}", None) for c, n in names.items()]


def fetch_gold():
    """قیمت جهانی طلا (از طریق PAX Gold که معادل یک اونس طلاست)"""
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": "pax-gold", "vs_currencies": "usd",
                "include_24hr_change": "true"},
        timeout=TIMEOUT,
    )
    d = r.json()["pax-gold"]
    ounce = d["usd"]
    ch = d.get("usd_24h_change")
    return [
        (fa("طلا - هر اونس"), f"${ounce:,.2f}", ch),
        (fa("طلا - هر گرم"), f"${ounce / 31.1035:,.2f}", ch),
    ]


def fetch_crypto():
    ids = {"bitcoin": "Bitcoin", "ethereum": "Ethereum", "tether": "Tether",
           "binancecoin": "BNB", "solana": "Solana", "ripple": "XRP",
           "dogecoin": "Dogecoin"}
    r = requests.get(
        "https://api.coingecko.com/api/v3/simple/price",
        params={"ids": ",".join(ids), "vs_currencies": "usd",
                "include_24hr_change": "true"},
        timeout=TIMEOUT,
    )
    data = r.json()
    return [(name, f"${data[i]['usd']:,.4f}".rstrip("0").rstrip("."),
             data[i].get("usd_24h_change")) for i, name in ids.items() if i in data]


def fetch_iran_market():
    """
    قیمت دلار بازار آزاد، سکه و طلای ایران (تومان).
    این‌ها API رایگان و رسمی ثابتی ندارن؛ آدرس سرویس مورد اعتمادت
    (یا API کلیددار) رو اینجا بذار و لیستی از (اسم، قیمت، تغییر) برگردون.
    مثال خروجی: [(fa("دلار آزاد"), "۱۲۰,۰۰۰ تومان", None)]
    """
    return []


SECTIONS = [
    ("ارز", fetch_fiat),
    ("طلا", fetch_gold),
    ("بازار ایران", fetch_iran_market),
    ("ارز دیجیتال", fetch_crypto),
]


# ---------------------------------------------------------------- رابط
def make_label(text, size=16, color=(1, 1, 1, 1), halign="left", bold=False):
    lb = Label(text=text, font_size=dp(size), color=color, font_name=FONT,
               halign=halign, valign="middle", bold=bold,
               size_hint_y=None, height=dp(size * 2.2))
    lb.bind(size=lambda w, s: setattr(w, "text_size", s))
    return lb


class PriceRow(BoxLayout):
    def __init__(self, name, price, change, **kw):
        super().__init__(size_hint_y=None, height=dp(44), padding=(dp(8), 0), **kw)
        self.add_widget(make_label(name, 16))
        self.add_widget(make_label(price, 16, halign="right", bold=True))
        if change is not None:
            col = (0.3, 0.85, 0.45, 1) if change >= 0 else (0.95, 0.35, 0.35, 1)
            self.add_widget(make_label(f"{change:+.2f}%", 13, col, "right"))


class PriceApp(App):
    def build(self):
        self.title = "All Prices"
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        root.add_widget(make_label(fa("قیمت همه چیز"), 22, halign="center", bold=True))

        self.scroll = ScrollView()
        self.box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        self.box.bind(minimum_height=self.box.setter("height"))
        self.scroll.add_widget(self.box)
        root.add_widget(self.scroll)

        self.status = make_label("", 12, (0.6, 0.6, 0.65, 1), "center")
        root.add_widget(self.status)

        btn = Button(text=fa("بروزرسانی"), font_name=FONT, size_hint_y=None,
                     height=dp(50), background_normal="",
                     background_color=(0.15, 0.45, 0.9, 1))
        btn.bind(on_release=lambda *_: self.refresh())
        root.add_widget(btn)

        Clock.schedule_once(lambda dt: self.refresh(), 0.3)
        Clock.schedule_interval(lambda dt: self.refresh(), 60)  # هر ۶۰ ثانیه
        return root

    def refresh(self):
        self.status.text = fa("در حال دریافت...")
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        results, errors = [], 0
        for title, fn in SECTIONS:
            try:
                rows = fn()
            except Exception:
                rows, errors = [], errors + 1
            results.append((title, rows))
        Clock.schedule_once(lambda dt: self._render(results, errors))

    def _render(self, results, errors):
        self.box.clear_widgets()
        for title, rows in results:
            if not rows:
                continue
            self.box.add_widget(make_label(fa(title), 18, (0.4, 0.7, 1, 1), bold=True))
            for name, price, ch in rows:
                self.box.add_widget(PriceRow(name, price, ch))
        msg = "بروزرسانی شد" if not errors else "بعضی بخش‌ها دریافت نشد (اینترنت؟)"
        self.status.text = fa(msg)


if __name__ == "__main__":
    PriceApp().run()
