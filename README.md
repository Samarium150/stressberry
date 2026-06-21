<p align="center">
  <a href="https://github.com/nschloe/stressberry"><img alt="stressberry" src="https://nschloe.github.io/stressberry/stressberry-logo.svg" width="60%"></a>
  <p align="center">Stress tests and temperature plots for the Raspberry Pi</p>
</p>

[![PyPI version](https://img.shields.io/pypi/v/stressberry.svg?style=flat-square)](https://pypi.org/project/stressberry)
[![Python versions](https://img.shields.io/badge/python-3.11%2B-blue?style=flat-square)](pyproject.toml)
[![GitHub stars](https://img.shields.io/github/stars/nschloe/stressberry.svg?style=flat-square&logo=github&label=Stars&logoColor=white)](https://github.com/nschloe/stressberry)

[![CI](https://github.com/nschloe/stressberry/actions/workflows/ci.yml/badge.svg)](https://github.com/nschloe/stressberry/actions/workflows/ci.yml)
[![codecov](https://img.shields.io/codecov/c/github/nschloe/stressberry.svg?style=flat-square)](https://codecov.io/gh/nschloe/stressberry)
[![Code style: Ruff](https://img.shields.io/badge/code%20style-ruff-46a?style=flat-square)](https://docs.astral.sh/ruff/)

There are a million ways to cool down your Raspberry Pi: Small heat sinks, specific
cases, and some [extreme DIY solutions](https://youtu.be/WfQMLInuwws). stressberry is a
package for testing the core temperature under different loads, and it produces nice
plots which can easily be compared.

### Raspberry Pi 4B
<img src="https://nschloe.github.io/stressberry/4b-active.svg" width="100%"> | <img src="https://nschloe.github.io/stressberry/4b-passive.svg" width="100%">
:--------------------------------------:|:----------------------:|
active | passive

<img src="https://nschloe.github.io/stressberry/rpi4-fans.jpg" width="70%"> | <img src="https://nschloe.github.io/stressberry/kksb.jpg" width="70%"> | <img src="https://nschloe.github.io/stressberry/argon-one.jpg" width="70%">
:--------------------------------------:|:----------------------:|:------:|
custom case with fans  (@flyingferret, [#21](https://github.com/nschloe/stressberry/issues/21))  | [KKSB case](https://kksb-cases.com/products/kksb-raspberry-pi-4-case-aluminium) (@JohBod, [#31](https://github.com/nschloe/stressberry/issues/31)) | [Argon One case](https://www.argon40.com/argon1/argon-one-pi4.html) (@jholloway, [#37](https://github.com/nschloe/stressberry/issues/37))
<img src="https://nschloe.github.io/stressberry/hex-wrench.png" width="70%"> | <img src="https://nschloe.github.io/stressberry/coolipi.jpg" width="70%"> | <img src="https://nschloe.github.io/stressberry/ice-tower.jpg" width="70%">
[hex wrench case](https://www.amazon.ca/Aluminum-Model-Raspberry-Wrench-Enclosure/dp/B07W6FT1DD?th=1) (@patrickpoirier51, [#45](https://github.com/nschloe/stressberry/issues/45)) | [CooliPi](https://www.coolipi.com/) (@CooliPi, [#47](https://github.com/nschloe/stressberry/issues/47), [#48](https://github.com/nschloe/stressberry/issues/48)) | [low-profile ice tower case](https://www.aliexpress.com/i/4000288119233.html) (@leonhess, [#54](https://github.com/nschloe/stressberry/issues/54))
<img src="https://nschloe.github.io/stressberry/flirc4b.jpeg" width="70%"> | <img src="https://nschloe.github.io/stressberry/armor.jpg" width="70%"> |
[Flirc case](https://flirc.tv/more/raspberry-pi-4-case) (@RichardKav, [#73](https://github.com/nschloe/stressberry/issues/73)) | [Armor Case](https://www.amazon.com/Geekworm-Raspberry-Computer-Aluminum-Compatible/dp/B07VD568FB) |


### Raspberry Pi 3B+
<img src="https://nschloe.github.io/stressberry/3b+.svg" width="70%">

#### FLIRC case

<img src="https://nschloe.github.io/stressberry/flirc-photo.jpg" width="30%">

The famous [FLIRC case](https://flirc.tv/more/raspberry-pi-case).
Thanks to @RichardKav for the measurements!

### Raspberry Pi 3B
<img src="https://nschloe.github.io/stressberry/3b.svg" width="70%">

<img src="https://nschloe.github.io/stressberry/naked-photo.jpg" width="90%"> | <img src="https://nschloe.github.io/stressberry/acryl-photo.jpg" width="90%"> | <img src="https://nschloe.github.io/stressberry/fasttech-photo.jpg" width="90%">
:-------------------:|:------------------:|:----------:|
No fans, heat sinks, or case. | Your average acrylic case from eBay. | [FastTech case](https://www.fasttech.com/p/5299000), full-body aluminum alloy with heat pads for CPU and RAM.

### How to

stressberry requires Python 3.11 or newer.

On Raspberry Pi OS, install the system tools first:

```bash
sudo apt install stress raspberrypi-utils
```

`stress` runs the CPU load test. `vcgencmd`, provided by `raspberrypi-utils`,
is used by default for CPU temperature and frequency measurements on Raspberry
Pi hardware. You can pass `--temperature-file` and `--frequency-file` if you
want to read those values from files instead.

Install the Python package with

```bash
python3 -m pip install stressberry
```

Users of [Arch Linux ARM](https://archlinuxarm.org/) can install from the official repos
```
[sudo] pacman -S stressberry
```

and run it with
```
stressberry-run out.dat
stressberry-plot out.dat -o out.png
```
(Use `MPLBACKEND=Agg stressberry-plot out.dat -o out.png` if you're running the script
headlessly on the Raspberry Pi itself.)

Ambient temperature measurement is optional. To use `stressberry-run --ambient`
with a DHT11, DHT22, or AM2302 sensor, install the optional sensor library:

```bash
python3 -m pip install Adafruit_DHT
```

If it your computer can't find the stressberry tools after installation,
you might have to add the directory `$HOME/.local/bin` to your path:
```
export PATH=$PATH:/home/pi/.local/bin
```
(You can also put this line in your `.bashrc`.)

The run lets the CPU idle for a bit, then stresses it with maximum load for 5 minutes,
and lets it cool down afterwards. The entire process takes 10 minutes.  The resulting
data is displayed to a screen or, if specified, written to a PNG file.

Generated data files are YAML documents with these top-level keys:

- `name`: label used in plots
- `time`: elapsed seconds from the first sample
- `temperature`: CPU temperature samples in degrees Celsius
- `cpu frequency`: CPU frequency samples in MHz
- `ambient`: ambient temperature samples in degrees Celsius, present when ambient
  measurement was requested

`time`, `temperature`, `cpu frequency`, and `ambient` contain parallel samples
when present. Older files without `cpu frequency` or `ambient` still work for
normal temperature plots. Delta-T plots require `ambient`, and frequency overlays
require `cpu frequency`. stressberry does not write an explicit schema or version
field to data files.

If you'd like to submit your own data for display here, feel free to [open an
issue](https://github.com/nschloe/stressberry/issues) and include the data file, a
photograph of your setup, and perhaps some further information.


### Development

Install [uv](https://docs.astral.sh/uv/) with the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Create the locked development environment with
```bash
uv sync --locked
```

Run the same checks as CI with
```bash
uv run ruff format --check .
uv run ruff check .
uv run pytest
```

Ruff is the linter and formatter for this project. Its configuration lives in
`pyproject.toml` under `[tool.ruff]` and `[tool.ruff.lint]`.

Build the source distribution and wheel with
```bash
uv build
```

Publishing releases to PyPI is out of scope for this modernization milestone.
CI builds and smoke-tests distributions, but it does not publish release
artifacts.

### License
This software is published under the [GPLv3 license](https://www.gnu.org/licenses/gpl-3.0.en.html).
