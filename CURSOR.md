Cursor Context — pkr.img

Architecture:
- web: Next.js App Router
- api: FastAPI + SQLAlchemy + SQLite (MVP)

Current flow:
- Host creates party, becomes first player
- Players join + upload image
- /party/{code}/upload stores Submission
- /party/{code}/end computes payouts

What we are building now (Phase 2):
CV backend pipeline that takes image_path and returns:
- total_cents
- breakdown_json

Constraints:
- Keep it simple/offline first
- Return debug artifacts optionally

CV Service Spec (Phase 2)

Goal:
Given an image of a player's chip stack, estimate:
- total value in cents
- per-denomination counts
- debug artifacts (optional)

Inputs:
- image file (jpg/png/webp)
- optional: table configuration (denomination values, colors)

Outputs (JSON):
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

Pipeline:
1) Detect individual chips (segmentation)
2) Cluster detections into stacks
3) Classify chip color/denomination
4) Sum totals

Success criteria:
- ±10% total error on average
- ±1 chip per stack for most stacks
