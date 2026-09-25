[app]
title = Currency Rates
package.name = currencyrates
package.domain = org.example

source.dir = .
source.include_exts = py,png,jpg,kv,atlas

version = 0.1
requirements = python3==3.10.14,kivy==2.3.0,requests
fullscreen = 0

android.permissions = INTERNET

[buildozer]
log_level = 2
warn_on_root = 1
