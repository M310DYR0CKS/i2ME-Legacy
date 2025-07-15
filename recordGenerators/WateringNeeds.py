import os
import shutil
import gzip
import logging
import coloredlogs
import xml.dom.minidom
import aiohttp
import aiofiles
import asyncio

from py2Lib import bit
import Util.MachineProductCfg as MPC
import records.LFRecord as LFR

# Logging setup
log = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=log)

TEMP_DIR = './.temp'
I2M_FILE = os.path.join(TEMP_DIR, 'WateringNeeds.i2m')
GZ_FILE = os.path.join(TEMP_DIR, 'WateringNeeds.gz')
API_KEY = "e1f10a1e78da46f5b10a1e78da96f525"

def get_location_data():
    return [
        (LFR.getCoopId(loc), LFR.getLatLong(loc).replace('/', ','))
        for loc in MPC.getPrimaryLocations()
    ]

async def fetch_watering_needs(session, coop_id, geocode):
    url = (
        f"https://api.weather.com/v2/indices/wateringNeeds/daypart/7day"
        f"?geocode={geocode}&language=en-US&format=xml&apiKey={API_KEY}"
    )
    try:
        async with session.get(url) as response:
            if response.status != 200:
                log.error(f"[{coop_id}] Failed with status code {response.status}")
                return ""
            raw = await response.text()
            trimmed = raw[63:-26]
            return (
                f'\n  <WateringNeeds id="000000000" locationKey="{coop_id}" isWxScan="0">\n'
                f'    {trimmed}\n'
                f'    <clientKey>{coop_id}</clientKey>\n'
                f'  </WateringNeeds>'
            )
    except Exception as e:
        log.exception(f"Error fetching for {coop_id}: {e}")
        return ""

async def make_watering_needs_record():
    os.makedirs(TEMP_DIR, exist_ok=True)

    log.info("Starting WateringNeeds record generation.")
    header = '<Data type="WateringNeeds">'
    footer = '</Data>'

    records = []

    async with aiohttp.ClientSession() as session:
        for coop_id, geocode in get_location_data():
            xml_fragment = await fetch_watering_needs(session, coop_id, geocode)
            if xml_fragment:
                records.append(xml_fragment)

    full_content = f"{header}{''.join(records)}{footer}"

    # Pretty print
    with open(I2M_FILE, 'w') as raw_file:
        raw_file.write(full_content)
    dom = xml.dom.minidom.parse(I2M_FILE)
    pretty = dom.toprettyxml(indent="  ")

    async with aiofiles.open(I2M_FILE, 'w') as f:
        await f.write(pretty[23:])  # Remove XML declaration

    # Compress to gzip
    with open(I2M_FILE, 'rb') as f_in, gzip.open(GZ_FILE, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    # Send to bit
    command = (
        f'<MSG>'
        f'<Exec workRequest="storeData(File={GZ_FILE},QGROUP=__WateringNeeds__,Feed=WateringNeeds)" />'
        f'<GzipCompressedMsg fname="WateringNeeds" />'
        f'</MSG>'
    )
    bit.sendFile([GZ_FILE], [command], 1, 0)

    # Cleanup
    os.remove(I2M_FILE)
    os.remove(GZ_FILE)
    log.info("WateringNeeds record completed and temp files removed.")

# Entry point
if __name__ == "__main__":
    asyncio.run(make_watering_needs_record())
