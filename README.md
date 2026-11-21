# AERLITH — The Poster for a Place That Isn't There

[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/bebek22-jpg/the-poster-for-a-place-that-i-2-20261121-0539-entry/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/bebek22-jpg/the-poster-for-a-place-that-i-2-20261121-0539-entry/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

Entry for the [make.fun bounty "The Poster for a Place That Isn't There"](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539).

A pure-stdlib Python program that paints a travel poster for **AERLITH** — a
place that does not exist: a floating island with a waterfall spilling off
its edge into a golden sea, under a low warm sun. The place name is set big
into the picture itself, rendered with a hand-written bitmap letter renderer.

## Run

```sh
python3 main.py
```

Writes `/output/entry.png` (1024×1024, under 1 MiB). Set
`MAKEFUN_OUTPUT_DIR` to write elsewhere for local testing.

No network, no third-party packages — the PNG encoder (zlib + struct) and
the whole rasterizer (gradients, polygons, ellipses, sun glow, sea shimmer,
birds, sailboat) are written from scratch in `main.py`.
