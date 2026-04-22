#!/usr/bin/env python3
from scripts.lib.common import SERVICES, YELLOW, RESET, run_command

def build(tag):
    print(f"{YELLOW}--- Building Docker Images ---{RESET}")
    for name, info in SERVICES.items():
        cmd = (
            f"docker build -t {info['image']}:{tag} -t {info['image']}:latest "
            f"-f {info['path']}/Dockerfile ."
        )
        run_command(cmd, f"Building {name} service")

def load_images_to_minikube(tag):
    print(f"{YELLOW}--- Loading images into Minikube ---{RESET}")
    for _, info in SERVICES.items():
        run_command(
            f"minikube image load {info['image']}:{tag}",
            f"Loading image {info['image']}:{tag} into Minikube",
        )
