# pkr.img — CV Service Spec (Phase 2)

## Goal
Given an image of a player's chip stack, estimate:
- total value in cents
- per-denomination counts
- debug artifacts (optional)

## Inputs
- image file (jpg/png/webp)
- optional: table configuration (denomination values, colors)

## Outputs (JSON)
```json
{
  "total_cents": 0,
  "breakdown": {
    "denom_1": 0,
    "denom_2": 0
  },
  "meta": {
    "model": "yolov8-seg",
    "confidence": 0.0,
    "notes": ""
  }
}
