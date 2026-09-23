"""Inspect exact skill, references, and model messages without running inference."""

import argparse
import json
from pathlib import Path

from harness.config import harness_version, load_config
from tutor.knowledge import knowledge_version
from tutor.models import TutorRequest
from tutor.service import PROMPT_VERSION, build_messages, sources_for_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="A TutorRequest JSON file")
    parser.add_argument("--harness", type=Path)
    args = parser.parse_args()
    request = TutorRequest.model_validate_json(args.request.read_text())
    config = load_config(args.harness)
    sources = sources_for_request(request, config)
    messages = build_messages(request, sources, config)
    print(
        json.dumps(
            {
                "harness_version": harness_version(config),
                "prompt_version": PROMPT_VERSION,
                "knowledge_version": knowledge_version(),
                "skill": config.skills[request.mode],
                "source_ids": [s.id for s in sources],
                "prompt_characters": sum(len(m["content"]) for m in messages),
                "messages": messages,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
