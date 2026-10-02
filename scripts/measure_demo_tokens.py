"""Measure selected synthetic prompts. The default run makes no model calls."""

import argparse
import base64
import hashlib
import json
import struct
import time
import zlib
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from demo_v1.exercise import BUGGY
from demo_v1.service import AskRequest, prepare
from llm_config import public_status
from providers import call_chat

ROOT = Path(__file__).resolve().parents[1]
BACKGROUND = (
    "Background example, not the current execution: A linear search visits array "
    "positions in order. A condition compares the value stored at a position with "
    "the target. A return ends the function. A failed comparison can lead to an "
    "index update and another iteration. Students can trace a small input and "
    "describe which positions the code visits before it returns. Keep hypothetical "
    "examples distinct from the recorded current state.\n"
)


def png(width, height):
    """Make four array bars with stdlib PNG encoding, without private image input."""

    def chunk(kind, data):
        return (
            struct.pack(">I", len(data))
            + kind
            + data
            + struct.pack(">I", zlib.crc32(kind + data))
        )

    rows = []
    for y in range(height):
        row = bytearray()
        for x in range(width):
            slot = min(3, x * 4 // width)
            left, right = (
                (slot * width // 4) + width // 40,
                ((slot + 1) * width // 4) - width // 40,
            )
            top = height - height * [4, 7, 2, 7][slot] // 8
            color = (25, 115, 105) if slot == 0 else (113, 139, 167)
            row.extend(
                color
                if left <= x < right and top <= y < height - height // 20
                else (245, 248, 250)
            )
        rows.append(b"\0" + row)
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(b"".join(rows)))
        + chunk(b"IEND", b"")
    )


def scenarios():
    question = "Why do I get -1 when 7 is in the array? Keep the answer short."
    for mode in ("hint", "explain", "debug"):
        request = AskRequest(
            code=BUGGY, values=[4, 7, 2, 7], target=7, question=question, mode=mode
        )
        yield "baseline-" + mode, prepare(request)[0], []
    history = [
        {"role": role, "content": (BACKGROUND * 8)[:1200]}
        for _ in range(4)
        for role in ("user", "assistant")
    ]
    request = AskRequest(
        code=BUGGY, values=[4, 7, 2, 7], target=7, question=question, history=history
    )
    yield "history-9600-chars", prepare(request)[0], []
    base = prepare(
        AskRequest(code=BUGGY, values=[4, 7, 2, 7], target=7, question=question)
    )[0]
    for chars in (20000, 80000):
        messages = [dict(m) for m in base]
        payload = json.loads(messages[-1]["content"])
        payload["supplementary_background"] = (
            BACKGROUND * (chars // len(BACKGROUND) + 1)
        )[:chars]
        messages[-1]["content"] = json.dumps(payload, ensure_ascii=False)
        yield f"extra-context-{chars}-chars", messages, []
    # The same text control isolates image plus content-part framing overhead.
    control = [dict(m) for m in base]
    control[-1]["content"] = [{"type": "text", "text": base[-1]["content"]}]
    yield "image-text-control", control, []
    for name, sizes in (
        ("one-image-384", [(384, 384)]),
        ("one-image-1536x768", [(1536, 768)]),
        ("four-images-384", [(384, 384)] * 4),
    ):
        messages = [dict(m) for m in base]
        parts = [{"type": "text", "text": base[-1]["content"]}]
        image_records = []
        for width, height in sizes:
            data = png(width, height)
            image_records.append(
                {
                    "width": width,
                    "height": height,
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
            parts.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,"
                        + base64.b64encode(data).decode()
                    },
                }
            )
        messages[-1]["content"] = parts
        yield name, messages, image_records


def text_chars(messages):
    total = 0
    for message in messages:
        content = message["content"]
        total += (
            len(content)
            if isinstance(content, str)
            else sum(len(p["text"]) for p in content if p["type"] == "text")
        )
    return total


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="Make one real provider request per selected scenario.",
    )
    parser.add_argument(
        "--case", action="append", help="Select scenario names. Omit to select all ten."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "artifacts" / "token-review" / "measurements.jsonl",
    )
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    selected = set(args.case or [])
    found = set()
    with args.output.open("a", encoding="utf-8") as output:
        for name, messages, images in scenarios():
            if selected and name not in selected:
                continue
            found.add(name)
            chars = text_chars(messages)
            record = {
                "case": name,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "live": args.live,
                "configuration": public_status(),
                "text_characters": chars,
                "text_token_estimate_range": [round(chars / 5), round(chars / 3)],
                "estimate_basis": "Rough character heuristic, not this model's tokenizer. Excludes image tokens and message framing.",
                "images": images,
                "prompt_sha256": hashlib.sha256(
                    json.dumps(messages, sort_keys=True).encode()
                ).hexdigest(),
            }
            if args.live:
                started = time.monotonic()
                try:
                    completion = call_chat(messages)
                    record["result"] = asdict(completion)
                    split_available = completion.reasoning_split_available
                    record["reasoning_split_available"] = split_available
                    if (
                        completion.output_tokens is not None
                        and split_available
                        and 0 <= completion.reasoning_tokens <= completion.output_tokens
                    ):
                        record["reported_non_reasoning_output_tokens"] = (
                            completion.output_tokens - completion.reasoning_tokens
                        )
                except Exception as exc:
                    record["error_type"] = type(exc).__name__
                    record["error"] = (
                        "Provider request failed. No credential or provider response body was recorded."
                    )
                record["latency_ms"] = round((time.monotonic() - started) * 1000)
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
            output.flush()
            print(json.dumps(record, ensure_ascii=False), flush=True)
    if selected - found:
        parser.error("Unknown case name: " + ", ".join(sorted(selected - found)))


if __name__ == "__main__":
    main()
