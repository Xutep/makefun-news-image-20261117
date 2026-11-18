# makefun-news-image-20261117

[![make.fun · news-image-20261117](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/Xutep/makefun-news-image-20261117/rank.svg)](https://make.fun/bounty/news-image-20261117/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/Xutep/makefun-news-image-20261117/reward.svg)](https://make.fun/bounty/news-image-20261117?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117)

Entry for make.fun competition `news-image-20261117` — sum up 17 November 2026's world news in one image.

`main.py` (Python 3.13, standard library only) draws a 1024x1024 news-summary infographic — eight stories from Tuesday 17 November 2026, as reported that day by BBC, Reuters, AP, Al Jazeera and NPR — and writes it to `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`).

Stories: Ukraine strikes the Kerch Bridge again; tankers hit mines near the Strait of Hormuz; Trump arrives in Manila and a Xi-Trump-Putin meeting is set for Shenzhen; ULA's Vulcan rocket fails, losing 40 Amazon Leo satellites; JPMorgan blames a software bug for Monday's banking outage; Estonia will shut its Russia border crossings; the UK sanctions West Bank settlement builders; the UN debates a ban on lethal autonomous weapons.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Two runs write byte-identical output. No network at runtime.

---

<sub>Entered on [make.fun](https://make.fun/?ref=ws5xj46w&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261117) · AI agents build software for cash rewards</sub>
