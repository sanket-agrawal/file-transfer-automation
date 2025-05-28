from fastapi import APIRouter, Query
from app.rclone_service import list_files, transfer_files, get_remotes

router = APIRouter(prefix="/rclone", tags=["Rclone"])

@router.get("/remotes")
def list_remotes():
    return get_remotes()

@router.get("/list")
def list_remote(remote: str = Query(...), path: str = Query("")):
    return list_files(remote, path)

@router.post("/transfer")
def transfer(
    src_remote: str = Query(...),
    src_path: str = Query(""),
    dest_remote: str = Query(...),
    dest_path: str = Query("")
):
    return transfer_files(src_remote, src_path, dest_remote, dest_path)
