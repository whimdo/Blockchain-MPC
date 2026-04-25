import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class GiteeConfig:
    access_token: str
    owner: str
    repo: str
    branch: str
    avatar_dir: str
    raw_base_url: str


def load_gitee_config() -> GiteeConfig:
    """Load Gitee image repository config from environment variables."""
    owner = os.getenv("GITEE_OWNER", "whim-du")
    repo = os.getenv("GITEE_REPO", "imgs")
    branch = os.getenv("GITEE_BRANCH", "main")
    avatar_dir = os.getenv("GITEE_AVATAR_DIR", "picgoImgs").strip("/")
    raw_base_url = os.getenv(
        "GITEE_RAW_BASE_URL",
        f"https://gitee.com/{owner}/{repo}/raw/{branch}/{avatar_dir}",
    ).rstrip("/")
    return GiteeConfig(
        access_token=os.getenv("GITEE_ACCESS_TOKEN", ""),
        owner=owner,
        repo=repo,
        branch=branch,
        avatar_dir=avatar_dir,
        raw_base_url=raw_base_url,
    )
