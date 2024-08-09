from config import (
    DISABLE_DOWNLOAD_ENDPOINT_AUTH,
    TINFOIL_WELCOME_MESSAGE
)
from decorators.auth import protected_route
from endpoints.responses.feeds import (
    WEBRCADE_SLUG_TO_TYPE_MAP,
    WEBRCADE_SUPPORTED_PLATFORM_SLUGS,
    TinfoilFeedFileSchema,
    TinfoilFeedSchema,
    WebrcadeFeedCategorySchema,
    WebrcadeFeedItemPropsSchema,
    WebrcadeFeedItemSchema,
    WebrcadeFeedSchema,
)
from fastapi import Request
from handler.database import db_platform_handler, db_rom_handler
from models.rom import Rom
from starlette.datastructures import URLPath
from utils.router import APIRouter
from handler.metadata.base_hander import (
    SWITCH_TITLEDB_REGEX,
    SWITCH_PRODUCT_ID_REGEX,
    MetadataHandler,
)

router = APIRouter()

@protected_route(
    router.get,
    "/webrcade/feed",
    [] if DISABLE_DOWNLOAD_ENDPOINT_AUTH else ["roms.read"],
)
def platforms_webrcade_feed(request: Request) -> WebrcadeFeedSchema:
    """Get webrcade feed endpoint
    https://docs.webrcade.com/feeds/format/

    Args:
        request (Request): Fastapi Request object

    Returns:
        WebrcadeFeedSchema: Webrcade feed object schema
    """

    platforms = db_platform_handler.get_platforms()

    categories = []
    for p in platforms:
        if p.slug not in WEBRCADE_SUPPORTED_PLATFORM_SLUGS:
            continue

        category_items = []
        for rom in db_rom_handler.get_roms(platform_id=p.id):
            category_item = WebrcadeFeedItemSchema(
                title=rom.name or "",
                description=rom.summary or "",
                type=WEBRCADE_SLUG_TO_TYPE_MAP.get(p.slug, p.slug),
                props=WebrcadeFeedItemPropsSchema(
                    rom=str(
                        request.url_for(
                            "get_rom_content",
                            id=rom.id,
                            file_name=rom.file_name,
                        )
                    ),
                ),
            )
            if rom.path_cover_s:
                category_item["thumbnail"] = str(
                    URLPath(
                        f"/assets/romm/resources/{rom.path_cover_s}"
                    ).make_absolute_url(request.base_url)
                )
            if rom.path_cover_l:
                category_item["background"] = str(
                    URLPath(
                        f"/assets/romm/resources/{rom.path_cover_l}"
                    ).make_absolute_url(request.base_url)
                )
            category_items.append(category_item)

        categories.append(
            WebrcadeFeedCategorySchema(
                title=p.name,
                longTitle=f"{p.name} Games",
                background=str(
                    URLPath(
                        f"/assets/webrcade/feed/{p.slug.lower()}-background.png"
                    ).make_absolute_url(request.base_url)
                ),
                thumbnail=str(
                    URLPath(
                        f"/assets/webrcade/feed/{p.slug.lower()}-thumb.png"
                    ).make_absolute_url(request.base_url)
                ),
                items=category_items,
            )
        )

    return WebrcadeFeedSchema(
        title="RomM Feed",
        longTitle="Custom RomM Feed",
        description="Custom feed from your RomM library",
        thumbnail="https://raw.githubusercontent.com/rommapp/romm/f2dd425d87ad8e21bf47f8258ae5dcf90f56fbc2/frontend/assets/isotipo.svg",
        background="https://raw.githubusercontent.com/rommapp/romm/release/.github/resources/screenshots/gallery.png",
        categories=categories,
    )

@protected_route(router.get, "/tinfoil/feed", ["roms.read"])
async def tinfoil_index_feed(request: Request, slug: str = "switch") -> TinfoilFeedSchema:
    """Get tinfoil custom index feed endpoint
    https://blawar.github.io/tinfoil/custom_index/

    Args:
        request (Request): Fastapi Request object
        slug (str, optional): Platform slug. Defaults to "switch".

    Returns:
        TinfoilFeedSchema: Tinfoil feed object schema
    """
    switch = db_platform_handler.get_platform_by_fs_slug(slug)
    if not switch:
        return TinfoilFeedSchema(
            files=[],
            directories=[],
            error="Nintendo Switch platform not found",
        )

    # Get the list of ROMs for the platform
    files: list[Rom] = db_rom_handler.get_roms(platform_id=switch.id)

    # Create the list of TinfoilFeedFileSchema objects
    file_list = []
    metadata_handler = MetadataHandler()

    for file in files:
        # Extract the title ID from the file name
        matchtitle = SWITCH_TITLEDB_REGEX.search(file.file_name)
        matchproduct = SWITCH_PRODUCT_ID_REGEX.search(file.file_name)
        if matchtitle:
            title_name, _ = await metadata_handler._switch_titledb_format(matchtitle, file.name)
            product_id, _ = await metadata_handler._switch_titledb_format(matchproduct, file.name)
            full_title = f"{title_name}"  # Append the title ID to the name
            full_product = f"{product_id}"
        else:
            full_title = file.name  # Use the original name if no title ID is found
            full_product = ""

        file_list.append(
            TinfoilFeedFileSchema(
                url=f"../../roms/{file.id}/content/{file.file_name}" + "#" + full_title + " [" + full_product + "].nsp",
                size=file.file_size_bytes
            )
        )

    return TinfoilFeedSchema(
        files=file_list,
        directories=[],
        success=TINFOIL_WELCOME_MESSAGE,
    )
