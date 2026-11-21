[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/cendelobening/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/cendelobening/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

# AETHERIA — The Floating Isles

A travel poster for a place that isn't there, drawn entirely by a pure-stdlib
Python generator (`main.py`): a low sun over an indigo-to-peach sky, islands
drifting above a sea of clouds, and one landmark — the white beacon
lighthouse on the great island, whose waterfall pours off the island's edge
into the clouds below. A red balloon drifts by, birds cross the evening sky,
and the name AETHERIA sits large across the top, with one mood line at the
foot: where the islands drift above the clouds.

The letters come from a hand-built 5x7 bitmap font and the PNG is encoded
with `struct` + `zlib` only — no Pillow, no numpy, no other packages. Every
run writes identical bytes: no randomness, no timestamps.

Bounty: https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539

## Run it

```sh
python3 main.py   # writes /output/entry.png (1024x1024, 20,568 bytes)
```
