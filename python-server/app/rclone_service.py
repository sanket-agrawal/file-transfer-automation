from rclone_python import rclone
import subprocess
import json

def get_remotes():
    try:
        result = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True)

        if result.returncode != 0:
            return {"error": result.stderr.strip()}

        remotes = [line.strip().rstrip(":") for line in result.stdout.strip().splitlines()]
        return {"remotes": remotes}
    
    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}

def list_files(remote: str, path: str = ""):
    full_path = f"{remote}:{path}" if path else f"{remote}:"
    try:
        result = subprocess.run(
            ["rclone", "lsjson", full_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        files = json.loads(result.stdout)
        return files
    except subprocess.CalledProcessError as e:
        return {"error": e.stderr.strip()}
    except json.JSONDecodeError as e:
        return {"error": "Failed to decode JSON output from rclone."}
    except Exception as e:
        return {"error": str(e)}

def transfer_files(src_remote: str, src_path: str, dest_remote: str, dest_path: str):
    src = f"{src_remote}:{src_path}".rstrip(":")
    dest = f"{dest_remote}:{dest_path}".rstrip(":")
    try:
        result = rclone.copy(src, dest, flags=["--progress"])
        return {"message": "Transfer successful", "details": result}
    except Exception as e:
        return {"error": str(e)}
