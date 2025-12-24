# pkr.img

> Turn a photo of your poker table into instant chip counts and Venmo settlements.

## Overview

pkr.img is a computer-vision–powered mobile app that analyzes a photo of a poker table, automatically detects and groups poker chips by player, estimates each player’s total, and generates Venmo-ready settlement instructions — all in seconds.

## Core Components

- **Vision Pipeline** — Detects and groups chips from an image
- **Settlement Engine** — Computes who pays who
- **Mobile App** — React Native interface for capture and results

## Roadmap

- [ ] Chip grouping MVP
- [ ] Denomination detection
- [ ] Settlement engine
- [ ] React Native app
- [ ] Venmo integration

## Tech Stack

- Python, OpenCV, PyTorch
- React Native (Expo)
- FastAPI
