import os
import sys
import gzip
import shutil
import logging
import coloredlogs
import xml.dom.minidom
import aiohttp
import aiofiles
import asyncio

# Module paths
sys.path.extend(["./py2lib", "./Util", "./records"])
import py2Lib.bit as bit
import MachineProductCfg as MPC
import LFRecord as LFR

# Logging
log = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=log)

# Constants
API_KEY = 'e1f10a1e78da46f5b10a1e78da96f525'
TEMP_DIR = './.temp'
I2M_FILE = os.path.join(TEMP_DIR, 'CurrentObservations.i2m')
GZ_FILE = os.path.join(TEMP_DIR, 'CurrentObservations.gz')


def get_location_data():
    """Return a list of (TECCI, ZIP) pairs from primary and metro cities."""
    locations = MPC.getPrimaryLocations() + MPC.getMetroCities()
    return [("T" + LFR.getCoopId(loc), LFR.getZip(loc)) for loc in locations]


async def fetch_current_observation(session, tecci, zip_code):
    url = (
        f"https://api.weather.com/v1/location/{zip_code}:4:US/observations/current.xml"
        f"?language=en-US&units=e&apiKey={API_KEY}"
    )
    log.debug(f"Fetching data for TECCI {tecci} (ZIP: {zip_code})")

    try:
        async with session.get(url) as response:
            if response.status != 200:
                log.error(f"[{tecci}] Failed request: HTTP {response.status}")
                return ""

            raw_xml = await response.text()

            # ⚠️ If this structure ever changes, slicing will break.
            sliced = raw_xml[67:-30]

            return (
                f'\n  <CurrentObservations id="000000000" locationKey="{tecci}" isWxscan="0">'
                f'\n    {sliced}\n    <clientKey>{tecci}</clientKey>\n  </CurrentObservations>'
            )

    except Exception as e:
        log.exception(f"Error fetching data for {tecci}: {e}")
        return ""


async def write_data_file():
    os.makedirs(TEMP_DIR, exist_ok=True)
    log.info("Starting CurrentObservations record generation.")

    locations = get_location_data()
    records = []

    async with aiohttp.ClientSession() as session:
        for tecci, zip_code in locations:
            record = await fetch_current_observation(session, tecci, zip_code)
            if record:
                records.append(record)

    # Write the combined XML document
    full_doc = '<Data type="CurrentObservations">' + ''.join(records) + '</Data>'

    with open(I2M_FILE, 'w') as f:
        f.write(full_doc)

    # Pretty-print it
    dom = xml.dom.minidom.parse(I2M_FILE)
    pretty = dom.toprettyxml(indent="  ")

    async with aiofiles.open(I2M_FILE, "w") as f:
        await f.write(pretty[23:])  # Trim <?xml ... ?> declaration

    # Compress XML to .gz
    with open(I2M_FILE, 'rb') as f_in, gzip.open(GZ_FILE, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Prepare BIT command and send
    command = (
        f'<MSG><Exec workRequest="storeData(File={GZ_FILE},QGROUP=__CurrentObservations__,Feed=CurrentObservations)" />'
        f'<GzipCompressedMsg fname="CurrentObservations" /></MSG>'
    )

    bit.sendFile([GZ_FILE], [command], 1, 0)

    # Clean up
    os.remove(I2M_FILE)
    os.remove(GZ_FILE)
    log.info("Finished processing and cleaned up temp files.")


if __name__ == "__main__":
    asyncio.run(write_data_file())
