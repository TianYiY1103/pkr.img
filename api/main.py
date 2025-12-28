from __future__ import annotations
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

import json
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from api.db import init_db, get_db
from api.models import Party, Player, Submission
from api.utils import generate_party_code
from api.cv_service import process_chip_image
import secrets

def new_host_token() -> str:
    return secrets.token_urlsafe(24)

app = FastAPI(title="pkr.img API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_ROOT = Path(__file__).parent / "uploads"


@app.on_event("startup")
def on_startup():
    init_db()
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)


@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------------
# Create Party
# -------------------------------
@app.post("/party")
def create_party(payload: dict):
    host_name = str(payload.get("host_name", "")).strip()
    host_venmo = payload.get("host_venmo")

    if not host_name:
        raise HTTPException(status_code=400, detail="host_name required")

    with get_db() as db:
        while True:
            code = generate_party_code()
            if not db.get(Party, code):
                break

        party = Party(code=code, host_token=new_host_token())
        db.add(party)
        db.commit()
        db.refresh(party)

        host_player = Player(
            party_code=code,
            name=host_name,
            venmo=host_venmo,
        )
        db.add(host_player)
        db.commit()
        db.refresh(host_player)

        party.host_player_id = host_player.id
        db.add(party)
        db.commit()
        db.refresh(party)

        return {
            "code": code,
            "host_token": party.host_token,
            "host_player_id": host_player.id,
        }


# -------------------------------
# Join Party
# -------------------------------
@app.post("/party/{code}/join")
def join_party(code: str, payload: dict):
    with get_db() as db:
        party = db.get(Party, code)
        if not party:
            raise HTTPException(status_code=404, detail="Party not found")

        if "name" not in payload or not str(payload["name"]).strip():
            raise HTTPException(status_code=400, detail="Missing player name")

        player = Player(
            party_code=code,
            name=payload["name"].strip(),
            venmo=payload.get("venmo"),
        )
        db.add(player)
        db.commit()
        db.refresh(player)

        return {"player_id": player.id}



# -------------------------------
# Upload Chip Photo
# -------------------------------
@app.post("/party/{code}/upload")
async def upload_photo(
    code: str,
    player_id: int = Form(...),
    image: UploadFile = File(...),
):
    # Basic content-type check (not bulletproof, but good MVP guardrail)
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    with get_db() as db:
        party = db.get(Party, code)
        if not party:
            raise HTTPException(status_code=404, detail="Party not found")

        player = db.get(Player, player_id)
        if not player or player.party_code != code:
            raise HTTPException(status_code=404, detail="Player not found in this party")

        # Save file
        party_dir = UPLOAD_ROOT / code
        party_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        ext = ".jpg"
        if image.content_type == "image/png":
            ext = ".png"
        elif image.content_type == "image/webp":
            ext = ".webp"

        filename = f"player{player_id}_{ts}{ext}"
        filepath = party_dir / filename

        contents = await image.read()
        filepath.write_bytes(contents)

        # Process image with CV service
        try:
            cv_result = process_chip_image(str(filepath))
            total_cents = cv_result.get("total_cents", 0)
            breakdown = cv_result.get("breakdown", {})
        except Exception as e:
            # Fallback to zeros if CV processing fails
            total_cents = 0
            breakdown = {}
            # Log error but don't fail the upload
            print(f"CV processing error: {e}")

        sub = Submission(
            party_code=code,
            player_id=player_id,
            image_path=str(filepath.relative_to(Path(__file__).parent)),
            total_cents=total_cents,
            breakdown_json=json.dumps(breakdown),
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)

        return {
            "submission_id": sub.id,
            "player_id": player_id,
            "image_path": sub.image_path,
            "total_cents": total_cents,
            "breakdown": breakdown,
        }

@app.get("/party/{code}")
def get_party(code: str):
    with get_db() as db:
        party = db.get(Party, code)
        if not party:
            raise HTTPException(status_code=404, detail="Party not found")

        def iso(dt):
            return dt.isoformat() if dt else None

        players = []
        # precompute submitted set (faster + cleaner)
        submitted_player_ids = {s.player_id for s in party.submissions}

        for p in party.players:
            players.append({
                "id": p.id,
                "name": p.name,
                "venmo": p.venmo,
                "submitted": p.id in submitted_player_ids,
                "created_at": iso(p.created_at),
            })

        submissions = []
        for s in party.submissions:
            submissions.append({
                "id": s.id,
                "player_id": s.player_id,
                "image_path": s.image_path,
                "total_cents": s.total_cents,
                "breakdown": json.loads(s.breakdown_json or "{}"),
                "created_at": iso(s.created_at),
            })

        return {
            "code": party.code,
            "created_at": iso(party.created_at),
            "ended_at": iso(party.ended_at),
            "players": players,
            "submissions": submissions,
        }


@app.post("/party/{code}/end")
def end_party(code: str, payload: dict):
    buy_in_cents = int(payload.get("buy_in_cents", 0))
    if buy_in_cents <= 0:
        raise HTTPException(status_code=400, detail="buy_in_cents must be > 0")

    host_token = str(payload.get("host_token", "")).strip()
    if not host_token:
        raise HTTPException(status_code=400, detail="host_token is required")

    with get_db() as db:
        party = db.get(Party, code)
        if not party:
            raise HTTPException(status_code=404, detail="Party not found")

        if host_token != party.host_token:
            raise HTTPException(status_code=403, detail="Host token invalid")

        # mark ended
        if party.ended_at is None:
            party.ended_at = datetime.utcnow()
            db.add(party)
            db.commit()
            db.refresh(party)

        # latest submission per player
        latest_by_player = {}
        for s in party.submissions:
            prev = latest_by_player.get(s.player_id)
            if prev is None or s.created_at > prev.created_at:
                latest_by_player[s.player_id] = s

        totals = []
        pnl = []
        for p in party.players:
            sub = latest_by_player.get(p.id)
            cash_out = sub.total_cents if sub else 0
            pnl_cents = cash_out - buy_in_cents

            totals.append({
                "player_id": p.id,
                "name": p.name,
                "venmo": p.venmo,
                "buy_in_cents": buy_in_cents,
                "cash_out_cents": cash_out,
                "pnl_cents": pnl_cents,
            })

            if pnl_cents != 0:
                pnl.append({
                    "player_id": p.id,
                    "name": p.name,
                    "venmo": p.venmo,
                    "pnl_cents": pnl_cents,
                })

        creditors = [x for x in pnl if x["pnl_cents"] > 0]
        debtors = [x for x in pnl if x["pnl_cents"] < 0]
        creditors.sort(key=lambda x: x["pnl_cents"], reverse=True)
        debtors.sort(key=lambda x: x["pnl_cents"])  # most negative first

        payments = []
        i = j = 0
        while i < len(debtors) and j < len(creditors):
            d = debtors[i]
            c = creditors[j]
            owe = -d["pnl_cents"]
            recv = c["pnl_cents"]
            amt = min(owe, recv)

            payments.append({
                "from_player_id": d["player_id"],
                "from_name": d["name"],
                "from_venmo": d["venmo"],
                "to_player_id": c["player_id"],
                "to_name": c["name"],
                "to_venmo": c["venmo"],
                "amount_cents": amt,
            })

            d["pnl_cents"] += amt
            c["pnl_cents"] -= amt
            if d["pnl_cents"] == 0:
                i += 1
            if c["pnl_cents"] == 0:
                j += 1

        return {
            "code": party.code,
            "ended_at": party.ended_at.isoformat() if party.ended_at else None,
            "buy_in_cents": buy_in_cents,
            "totals": totals,
            "payments": payments,
        }