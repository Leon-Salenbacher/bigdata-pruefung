import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile


REPO_DIR = Path(__file__).resolve().parents[1]


def main():
    container = json.loads(subprocess.check_output(
        ["docker", "inspect", os.environ["HOSTNAME"]],
        text=True,
    ))[0]

    project = container["Config"]["Labels"]["com.docker.compose.project"]

    host_repo = next(
        mount["Source"]
        for mount in container["Mounts"]
        if mount["Destination"] == str(REPO_DIR)
    )

    compose = ["docker", "compose", "--project-name", project]

    config = json.loads(subprocess.check_output(
        compose + [
            "--file", str(REPO_DIR / "docker-compose.yml"),
            "--profile", "download",
            "--profile", "tools",
            "config", "--format", "json",
        ],
        cwd=REPO_DIR,
        text=True,
    ))

    # Bind-Mounts benötigt Docker auf dem Host.
    # Build-Kontexte liest dagegen die CLI im Airflow-Container.
    for service in config["services"].values():
        for volume in service.get("volumes", []):
            if volume["type"] != "bind":
                continue

            try:
                relative = PurePosixPath(volume["source"]).relative_to(
                    str(REPO_DIR)
                )
            except ValueError:
                continue

            volume["source"] = str(PurePosixPath(host_repo) / relative)

    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "compose.json"
        config_path.write_text(json.dumps(config), encoding="utf-8")

        return subprocess.call(
            compose + [
                "--project-directory", str(REPO_DIR),
                "--file", str(config_path),
            ] + sys.argv[1:],
            cwd=REPO_DIR,
        )


if __name__ == "__main__":
    sys.exit(main())