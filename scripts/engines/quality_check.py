#!/usr/bin/env python3
import subprocess
from scripts.lib.common import SERVICES, YELLOW, BLUE, GREEN, RESET, CHART_PATH, run_command

def format_code():
    print(f"{YELLOW}--- Formatting Codebase ---{RESET}")
    for name, info in SERVICES.items():
        run_command(f"cd {info['path']} && go fmt ./...", f"Formatting Go {name} service")
    run_command("cd shared && go fmt ./...", "Formatting Go shared module")
    
    if subprocess.run("which black", shell=True, capture_output=True).returncode == 0:
        run_command("black manage.py scripts/*.py", "Formatting Python scripts")
    else:
        print(f"{BLUE}  Skip Python formatting (black not found){RESET}")
    print(f"{GREEN}Format complete.{RESET}")

def lint():
    print(f"{YELLOW}--- Linting Helm Charts ---{RESET}")
    run_command(f"helm lint {CHART_PATH}", "Helm linting")

def tidy():
    print(f"{YELLOW}--- Tidy Go Modules ---{RESET}")
    for name, info in SERVICES.items():
        run_command(f"cd {info['path']} && go mod tidy", f"Tidying {name} service")
    run_command("cd shared && go mod tidy", "Tidying shared module")

def check():
    print(f"{YELLOW}--- Running check suite (fmt + lint + tidy) ---{RESET}")
    format_code()
    lint()
    tidy()
