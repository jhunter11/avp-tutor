"""Server-side, reproducible harness configuration. Clients cannot select files."""

import hashlib
import os
from pathlib import Path

from pydantic import Field, PrivateAttr, model_validator

from tutor.models import StrictModel

ROOT = Path(__file__).resolve().parent


class HarnessConfig(StrictModel):
    name: str = Field(min_length=1, max_length=100)
    retrieval_k: int = Field(default=3, ge=1, le=6)
    include_prior_question: bool = True
    skills: dict[str, str]
    _texts: dict[str, str] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def validate_skills(self):
        if set(self.skills) != {"explain", "hint", "predict", "debug"}:
            raise ValueError("Each tutor mode must have exactly one skill")
        for filename in self.skills.values():
            if Path(filename).name != filename or not filename.endswith(".md"):
                raise ValueError(
                    "Skills must be Markdown filenames inside harness/skills"
                )
            path = ROOT / "skills" / filename
            if (
                not path.is_file()
                or path.resolve().parent != (ROOT / "skills").resolve()
            ):
                raise ValueError("Unknown skill file")
            if path.stat().st_size > 8000:
                raise ValueError("Skill exceeds 8000 bytes")
        self._texts = {
            mode: (ROOT / "skills" / filename).read_text()
            for mode, filename in self.skills.items()
        }
        return self


def load_config(path: Path | None = None):
    selected = path or Path(
        os.environ.get("HARNESS_CONFIG", str(ROOT / "configs" / "baseline.json"))
    )
    return HarnessConfig.model_validate_json(selected.read_text())


def skill_text(config, mode):
    return config._texts[mode]


def harness_version(config):
    content = config.model_dump_json() + "".join(
        skill_text(config, mode) for mode in sorted(config.skills)
    )
    return hashlib.sha256(content.encode()).hexdigest()[:12]
