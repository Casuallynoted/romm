from starlette.datastructures import URLPath
from utils.router import APIRouter
from handler.metadata.base_hander import (
    SWITCH_TITLEDB_REGEX,
    MetadataHandler,
)

router = APIRouter()
async def _switch_productid_format(
        self, match: re.Match[str], search_term: str
    ) -> tuple[str, dict | None]:
        product_id = match.group(1)

        # Game updates have the same product ID as the main application, except with bitmask 0x800 set
        product_id = list(product_id)
        product_id[-3] = "0"
        product_id = "".join(product_id)

        if not (await async_cache.exists(SWITCH_PRODUCT_ID_KEY)):
            log.warning("Fetching the Switch productID index file...")
            await update_switch_titledb_task.run(force=True)

            if not (await async_cache.exists(SWITCH_PRODUCT_ID_KEY)):
                log.error("Could not fetch the Switch productID index file")
                return search_term, None

        index_entry = await async_cache.hget(SWITCH_PRODUCT_ID_KEY, product_id)
        if index_entry:
            index_entry = json.loads(index_entry)
            return index_entry["id"], index_entry

@protected_route(
    router.get,
@@ -156,24 +133,10 @@ async def tinfoil_index_feed(request: Request, slug: str = "switch") -> TinfoilF
    metadata_handler = MetadataHandler()

    for file in files:
        # Extract the title ID from the file name
        matchtitle = SWITCH_TITLEDB_REGEX.search(file.file_name)
        full_product = ""

        if matchtitle:
            title_name, _ = await metadata_handler._switch_titledb_format(matchtitle, file.name)
            full_title = f"{title_name}"  # Append the title ID to the name

            # Get product ID using _switch_productid_format
            product_id, _ = await metadata_handler._switch_productid_format(matchtitle, file.file_name)
            if product_id:
                full_product = product_id  # Use the retrieved product ID
        else:
            full_title = file.name  # Use the original name if no title ID is found

        file_list.append(
            TinfoilFeedFileSchema(
                url=f"../../roms/{file.id}/content/{file.file_name}" + "#" + full_title + " [" + full_product + "].nsp",
                url=f"../../roms/{file.id}/content/{file.file_name}",
                size=file.file_size_bytes
            )
        )
)
