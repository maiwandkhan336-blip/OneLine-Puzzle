[app]

title = OneLine Puzzle
package.name = onelinepuzzle
package.domain = org.onelinepuzzle

source.dir = .
source.include_exts = py,wav,png,jpg,json

version = 1.0.0
requirements = python3,kivy

orientation = portrait
fullscreen = 0

android.api = 35
android.minapi = 23
android.ndk = 27c

android.archs = arm64-v8a, armeabi-v7a

android.permissions = VIBRATE

[buildozer]

log_level = 2
warn_on_root = 1
