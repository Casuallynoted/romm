import binascii
from base64 import b64encode
from datetime import datetime, timezone
from io import BytesIO
from shutil import rmtree
from typing import Any
from urllib.parse import quote

from anyio import Path
from config import (
    DEV_MODE,
    DISABLE_DOWNLOAD_ENDPOINT_AUTH,
    LIBRARY_BASE_PATH,
    RESOURCES_BASE_PATH,
)
from decorators.auth import protected_route
from endpoints.responses import MessageResponse
from endpoints.responses.rom import DetailedRomSchema, RomUserSchema, SimpleRomSchema
from exceptions.endpoint_exceptions import RomNotFoundInDatabaseException
from exceptions.fs_exceptions import RomAlreadyExistsException
from fastapi import HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from handler.auth.constants import Scope
from handler.database import db_collection_handler, db_platform_handler, db_rom_handler
from handler.filesystem import fs_resource_handler, fs_rom_handler
from handler.filesystem.base_handler import CoverSize
from handler.metadata import meta_igdb_handler, meta_moby_handler
from logger.logger import log
from models.rom import Rom, RomUser
from PIL import Image
from starlette.requests import ClientDisconnect
from starlette.responses import FileResponse
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import FileTarget, NullTarget
from utils.filesystem import sanitize_filename
from utils.hashing import crc32_to_hex
from utils.nginx import FileRedirectResponse, ZipContentLine, ZipResponse
from utils.router import APIRouter

router = APIRouter()


@protected_route(router.post, "/roms", [Scope.ROMS_WRITE])
async def add_rom(request: Request):
    """Upload single rom endpoint

    Args:
        request (Request): Fastapi Request object

    Raises:
        HTTPException: No files were uploaded
    """
    platform_id = request.headers.get("x-upload-platform")
    filename = request.headers.get("x-upload-filename")
    if not platform_id or not filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No platform ID or filename provided",
        ) from None

    db_platform = db_platform_handler.get_platform(int(platform_id))
    if not db_platform:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Platform not found",
        ) from None

    platform_fs_slug = db_platform.fs_slug
    roms_path = fs_rom_handler.build_upload_fs_path(platform_fs_slug)
    log.info(f"Uploading file to {platform_fs_slug}")

    file_location = Path(f"{roms_path}/{filename}")
    parser = StreamingFormDataParser(headers=request.headers)
    parser.register("x-upload-platform", NullTarget())
    parser.register(filename, FileTarget(str(file_location)))

    if await file_location.exists():
        log.warning(f" - Skipping {filename} since the file already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File {filename} already exists",
        ) from None

    async def cleanup_partial_file():
        if await file_location.exists():
            await file_location.unlink()

    try:
        async for chunk in request.stream():
            parser.data_received(chunk)
    except ClientDisconnect:
        log.error("Client disconnected during upload")
        await cleanup_partial_file()
    except Exception as exc:
        log.error("Error uploading files", exc_info=exc)
        await cleanup_partial_file()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file(s)",
        ) from exc

    return Response(status_code=status.HTTP_201_CREATED)


@protected_route(router.get, "/roms", [Scope.ROMS_READ])
def get_roms(
    request: Request,
    platform_id: int | None = None,
    collection_id: int | None = None,
    search_term: str = "",
    limit: int | None = None,
    offset: int | None = None,
    order_by: str = "name",
    order_dir: str = "asc",
) -> list[SimpleRomSchema]:
    """Get roms endpoint

    Args:
        request (Request): Fastapi Request object
        platform_id (int, optional): Platform ID to filter ROMs
        collection_id (int, optional): Collection ID to filter ROMs
        search_term (str, optional): Search term to filter ROMs
        limit (int, optional): Limit the number of ROMs returned
        offset (int, optional): Offset for pagination
        order_by (str, optional): Field to order ROMs by
        order_dir (str, optional): Direction to order ROMs (asc or desc)
        last_played (bool, optional): Flag to filter ROMs by last played

    Returns:
        list[DetailedRomSchema]: List of ROMs stored in the database
    """

    if hasattr(Rom, order_by):
        roms = db_rom_handler.get_roms(
            platform_id=platform_id,
            collection_id=collection_id,
            search_term=search_term.lower(),
            order_by=order_by.lower(),
            order_dir=order_dir.lower(),
            limit=limit,
            offset=offset,
        )
    elif hasattr(RomUser, order_by):
        roms = db_rom_handler.get_roms_user(
            user_id=request.user.id,
            platform_id=platform_id,
            collection_id=collection_id,
            search_term=search_term,
            order_by=order_by,
            order_dir=order_dir,
            limit=limit,
            offset=offset,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order_by field",
        )

    roms = [SimpleRomSchema.from_orm_with_request(rom, request) for rom in roms]
    return [rom for rom in roms if rom]


@protected_route(
    router.get,
    "/roms/{id}",
    [] if DISABLE_DOWNLOAD_ENDPOINT_AUTH else [Scope.ROMS_READ],
)
def get_rom(request: Request, id: int) -> DetailedRomSchema:
    """Get rom endpoint

    Args:
        request (Request): Fastapi Request object
        id (int): Rom internal id

    Returns:
        DetailedRomSchema: Rom stored in the database
    """

    rom = db_rom_handler.get_rom(id)

    if not rom:
        raise RomNotFoundInDatabaseException(id)

    return DetailedRomSchema.from_orm_with_request(rom, request)


@protected_route(
    router.head,
    "/roms/{id}/content/{file_name}",
    [] if DISABLE_DOWNLOAD_ENDPOINT_AUTH else [Scope.ROMS_READ],
)
async def head_rom_content(
    request: Request,
    id: int,
    file_name: str,
):
    """Head rom content endpoint

    Args:
        request (Request): Fastapi Request object
        id (int): Rom internal id
        file_name (str): File name to download
        file_ids (list[int]): List of file ids to download for multi-part roms

    Returns:
        FileResponse: Returns the response with headers
    """

    rom = db_rom_handler.get_rom(id)

    if not rom:
        raise RomNotFoundInDatabaseException(id)

    file_ids = request.query_params.get("file_ids") or ""
    file_ids = [int(f) for f in file_ids.split(",") if f]
    files = db_rom_handler.get_rom_files(rom.id)
    files = [f for f in files if f.id in file_ids or not file_ids]

    # Serve the file directly in development mode for emulatorjs
    if DEV_MODE:
        if not rom.multi:
            rom_path = f"{LIBRARY_BASE_PATH}/{rom.full_path}"
            return FileResponse(
                path=rom_path,
                filename=rom.fs_name,
                headers={
                    "Content-Disposition": f'attachment; filename="{quote(rom.fs_name)}"',
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(rom.fs_size_bytes),
                },
            )

        if len(files) == 1:
            file = files[0]
            rom_path = f"{LIBRARY_BASE_PATH}/{file.full_path}"
            return FileResponse(
                path=rom_path,
                filename=file.file_name,
                headers={
                    "Content-Disposition": f'attachment; filename="{quote(file.file_name)}"',
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(file.file_size_bytes),
                },
            )

        return Response(
            headers={
                "Content-Type": "application/zip",
                "Content-Disposition": f'attachment; filename="{quote(file_name)}.zip"',
            },
        )

    # Otherwise proxy through nginx
    if not rom.multi:
        return FileRedirectResponse(
            download_path=Path(f"/library/{rom.full_path}"),
            filename=rom.fs_name,
        )

    if len(files) == 1:
        return FileRedirectResponse(
            download_path=Path(f"/library/{files[0].full_path}"),
        )

    return Response(
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{quote(file_name)}.zip"',
        },
    )


@protected_route(
    router.get,
    "/roms/{id}/content/{file_name}",
    [] if DISABLE_DOWNLOAD_ENDPOINT_AUTH else [Scope.ROMS_READ],
)
async def get_rom_content(
    request: Request,
    id: int,
    file_name: str,
):
    """Download rom endpoint (one single file or multiple zipped files for multi-part roms)

    Args:
        request (Request): Fastapi Request object
        id (int): Rom internal id
        file_name: Zip file output name

    Returns:
        FileResponse: Returns one file for single file roms

    Yields:
        ZipResponse: Returns a response for nginx to serve a Zip file for multi-part roms
    """

    current_username = request.user.username if request.user else "unknown"
    rom = db_rom_handler.get_rom(id)

    if not rom:
        raise RomNotFoundInDatabaseException(id)

    file_ids = request.query_params.get("file_ids") or ""
    file_ids = [int(f) for f in file_ids.split(",") if f]
    files = db_rom_handler.get_rom_files(rom.id)
    files = [f for f in files if f.id in file_ids or not file_ids]

    log.info(f"User {current_username} is downloading {rom.fs_name}")

    # Serve the file directly in development mode for emulatorjs
    if DEV_MODE:
        if not rom.multi:
            rom_path = f"{LIBRARY_BASE_PATH}/{rom.full_path}"
            return FileResponse(
                path=rom_path,
                filename=rom.fs_name,
                headers={
                    "Content-Disposition": f'attachment; filename="{quote(rom.fs_name)}"',
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(rom.fs_size_bytes),
                },
            )

        if len(files) == 1:
            file = files[0]
            rom_path = f"{LIBRARY_BASE_PATH}/{file.full_path}"
            return FileResponse(
                path=rom_path,
                filename=file.file_name,
                headers={
                    "Content-Disposition": f'attachment; filename="{quote(file.file_name)}"',
                    "Content-Type": "application/octet-stream",
                    "Content-Length": str(file.file_size_bytes),
                },
            )

        content_lines = [
            ZipContentLine(
                crc32=f.crc_hash,
                size_bytes=(await Path(LIBRARY_BASE_PATH, f.full_path).stat()).st_size,
                encoded_location=quote(f"{LIBRARY_BASE_PATH}/{f.full_path}"),
                filename=f.full_path.replace(rom.full_path, ""),
            )
            for f in files
        ]

        return ZipResponse(
            content_lines=content_lines,
            filename=f"{quote(file_name)}.zip",
        )

    # Otherwise proxy through nginx
    if not rom.multi:
        return FileRedirectResponse(
            download_path=Path(f"/library/{rom.full_path}"),
            filename=rom.fs_name,
        )

    if len(files) == 1:
        return FileRedirectResponse(
            download_path=Path(f"/library/{files[0].full_path}"),
        )

    content_lines = [
        ZipContentLine(
            crc32=f.crc_hash,
            size_bytes=(await Path(LIBRARY_BASE_PATH, f.full_path).stat()).st_size,
            encoded_location=quote(f"/library-zip/{f.full_path}"),
            filename=f.full_path.replace(rom.full_path, ""),
        )
        for f in files
    ]

    m3u_encoded_content = "\n".join(
        [f.full_path.replace(rom.full_path, "") for f in files]
    ).encode()
    m3u_base64_content = b64encode(m3u_encoded_content).decode()
    m3u_line = ZipContentLine(
        crc32=crc32_to_hex(binascii.crc32(m3u_encoded_content)),
        size_bytes=len(m3u_encoded_content),
        encoded_location=f"/decode?value={m3u_base64_content}",
        filename=f"{file_name}.m3u",
    )

    return ZipResponse(
        content_lines=content_lines + [m3u_line],
        filename=f"{quote(file_name)}.zip",
    )


@protected_route(router.put, "/roms/{id}", [Scope.ROMS_WRITE])
async def update_rom(
    request: Request,
    id: int,
    rename_as_source: bool = False,
    remove_cover: bool = False,
    artwork: UploadFile | None = None,
    unmatch_metadata: bool = False,
) -> DetailedRomSchema:
    """Update rom endpoint

    Args:
        request (Request): Fastapi Request object
        id (Rom): Rom internal id
        rename_as_source (bool, optional): Flag to rename rom file as matched IGDB game. Defaults to False.
        artwork (UploadFile, optional): Custom artork to set as cover. Defaults to File(None).
        unmatch_metadata: Remove the metadata matches for this game. Defaults to False.

    Raises:
        HTTPException: If a rom already have that name when enabling the rename_as_source flag

    Returns:
        DetailedRomSchema: Rom stored in the database
    """

    data = await request.form()

    rom = db_rom_handler.get_rom(id)

    if not rom:
        raise RomNotFoundInDatabaseException(id)

    if unmatch_metadata:
        db_rom_handler.update_rom(
            id,
            {
                "igdb_id": None,
                "sgdb_id": None,
                "moby_id": None,
                "name": rom.fs_name,
                "summary": "",
                "url_screenshots": [],
                "path_screenshots": [],
                "path_cover_s": "",
                "path_cover_l": "",
                "url_cover": "",
                "slug": "",
                "igdb_metadata": {},
                "moby_metadata": {},
                "revision": "",
            },
        )

        rom = db_rom_handler.get_rom(id)
        if not rom:
            raise RomNotFoundInDatabaseException(id)

        return DetailedRomSchema.from_orm_with_request(rom, request)

    cleaned_data: dict[str, Any] = {
        "igdb_id": data.get("igdb_id", rom.igdb_id),
        "moby_id": data.get("moby_id", rom.moby_id),
    }

    moby_id = cleaned_data["moby_id"]
    if moby_id and int(moby_id) != rom.moby_id:
        moby_rom = await meta_moby_handler.get_rom_by_id(int(moby_id))
        cleaned_data.update(moby_rom)
        path_screenshots = await fs_resource_handler.get_rom_screenshots(
            rom=rom,
            url_screenshots=cleaned_data.get("url_screenshots", []),
        )
        cleaned_data.update({"path_screenshots": path_screenshots})

    igdb_id = cleaned_data["igdb_id"]
    if igdb_id and int(igdb_id) != rom.igdb_id:
        igdb_rom = await meta_igdb_handler.get_rom_by_id(int(igdb_id))
        cleaned_data.update(igdb_rom)
        path_screenshots = await fs_resource_handler.get_rom_screenshots(
            rom=rom,
            url_screenshots=cleaned_data.get("url_screenshots", []),
        )
        cleaned_data.update({"path_screenshots": path_screenshots})

    cleaned_data.update(
        {
            "name": data.get("name", rom.name),
            "summary": data.get("summary", rom.summary),
        }
    )

    new_fs_name = str(data.get("fs_name") or rom.fs_name)

    try:
        if rename_as_source:
            new_fs_name = rom.fs_name.replace(
                rom.fs_name_no_tags or rom.fs_name_no_ext,
                str(data.get("name") or rom.name),
            )
            new_fs_name = sanitize_filename(new_fs_name)
            fs_rom_handler.rename_fs_rom(
                old_name=rom.fs_name,
                new_name=new_fs_name,
                fs_path=rom.fs_path,
            )
        elif rom.fs_name != new_fs_name:
            new_fs_name = sanitize_filename(new_fs_name)
            fs_rom_handler.rename_fs_rom(
                old_name=rom.fs_name,
                new_name=new_fs_name,
                fs_path=rom.fs_path,
            )
    except RomAlreadyExistsException as exc:
        log.error(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=exc
        ) from exc

    cleaned_data.update(
        {
            "fs_name": new_fs_name,
            "fs_name_no_tags": fs_rom_handler.get_file_name_with_no_tags(new_fs_name),
            "fs_name_no_ext": fs_rom_handler.get_file_name_with_no_extension(
                new_fs_name
            ),
        }
    )

    if remove_cover:
        cleaned_data.update(fs_resource_handler.remove_cover(rom))
        cleaned_data.update({"url_cover": ""})
    else:
        if artwork is not None and artwork.filename is not None:
            file_ext = artwork.filename.split(".")[-1]
            (
                path_cover_l,
                path_cover_s,
                artwork_path,
            ) = await fs_resource_handler.build_artwork_path(rom, file_ext)

            cleaned_data.update(
                {"path_cover_s": path_cover_s, "path_cover_l": path_cover_l}
            )

            artwork_content = BytesIO(await artwork.read())
            file_location_small = Path(f"{artwork_path}/small.{file_ext}")
            file_location_large = Path(f"{artwork_path}/big.{file_ext}")
            with Image.open(artwork_content) as img:
                img.save(file_location_large)
                fs_resource_handler.resize_cover_to_small(
                    img, save_path=file_location_small
                )

            cleaned_data.update({"url_cover": ""})
        else:
            if data.get("url_cover", "") != rom.url_cover or not (
                await fs_resource_handler.cover_exists(rom, CoverSize.BIG)
            ):
                cleaned_data.update({"url_cover": data.get("url_cover", rom.url_cover)})
                path_cover_s, path_cover_l = await fs_resource_handler.get_cover(
                    overwrite=True,
                    entity=rom,
                    url_cover=str(data.get("url_cover") or ""),
                )
                cleaned_data.update(
                    {"path_cover_s": path_cover_s, "path_cover_l": path_cover_l}
                )

    db_rom_handler.update_rom(id, cleaned_data)
    rom = db_rom_handler.get_rom(id)
    if not rom:
        raise RomNotFoundInDatabaseException(id)

    return DetailedRomSchema.from_orm_with_request(rom, request)


@protected_route(router.post, "/roms/delete", [Scope.ROMS_WRITE])
async def delete_roms(
    request: Request,
) -> MessageResponse:
    """Delete roms endpoint

    Args:
        request (Request): Fastapi Request object.
            {
                "roms": List of rom's ids to delete
            }
        delete_from_fs (bool, optional): Flag to delete rom from filesystem. Defaults to False.

    Returns:
        MessageResponse: Standard message response
    """

    data: dict = await request.json()
    roms_ids: list = data["roms"]
    delete_from_fs: list = data["delete_from_fs"]

    for id in roms_ids:
        rom = db_rom_handler.get_rom(id)

        if not rom:
            raise RomNotFoundInDatabaseException(id)

        log.info(f"Deleting {rom.fs_name} from database")
        db_rom_handler.delete_rom(id)

        # Update collections to remove the deleted rom
        collections = db_collection_handler.get_collections_by_rom_id(id)
        for collection in collections:
            collection.roms = {rom_id for rom_id in collection.roms if rom_id != id}
            db_collection_handler.update_collection(
                collection.id, {"roms": collection.roms}
            )

        try:
            rmtree(f"{RESOURCES_BASE_PATH}/{rom.fs_resources_path}")
        except FileNotFoundError:
            log.error(f"Couldn't find resources to delete for {rom.name}")

        if id in delete_from_fs:
            log.info(f"Deleting {rom.fs_name} from filesystem")
            try:
                fs_rom_handler.remove_from_fs(fs_path=rom.fs_path, fs_name=rom.fs_name)
            except FileNotFoundError as exc:
                error = (
                    f"Rom file {rom.fs_name} not found for platform {rom.platform_slug}"
                )
                log.error(error)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=error
                ) from exc

    return {"msg": f"{len(roms_ids)} roms deleted successfully!"}


@protected_route(router.put, "/roms/{id}/props", [Scope.ROMS_USER_WRITE])
async def update_rom_user(request: Request, id: int) -> RomUserSchema:
    data = await request.json()
    rom_user_data = data.get("data", {})

    rom = db_rom_handler.get_rom(id)

    if not rom:
        raise RomNotFoundInDatabaseException(id)

    db_rom_user = db_rom_handler.get_rom_user(
        id, request.user.id
    ) or db_rom_handler.add_rom_user(id, request.user.id)

    fields_to_update = [
        "note_raw_markdown",
        "note_is_public",
        "is_main_sibling",
        "backlogged",
        "now_playing",
        "hidden",
        "rating",
        "difficulty",
        "completion",
        "status",
    ]

    cleaned_data = {
        field: rom_user_data[field]
        for field in fields_to_update
        if field in rom_user_data
    }

    if data.get("update_last_played", False):
        cleaned_data.update({"last_played": datetime.now(timezone.utc)})
    elif data.get("remove_last_played", False):
        cleaned_data.update({"last_played": None})

    rom_user = db_rom_handler.update_rom_user(db_rom_user.id, cleaned_data)

    return RomUserSchema.model_validate(rom_user)
