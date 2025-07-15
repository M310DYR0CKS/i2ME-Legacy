import asyncio
import aiohttp
import aiofiles
import gzip
import os
import shutil
import xml.dom.minidom
import logging
import coloredlogs
import sys

# Path setup
sys.path.extend(["./py2lib", "./Util", "./records"])

# Custom modules
import bit
import MachineProductCfg as MPC
import LFRecord as LFR

# Logging setup
log = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=log)

API_KEY = 'e1f10a1e78da46f5b10a1e78da96f525'
TEMP_PATH = './.temp'
I2M_FILE = os.path.join(TEMP_PATH, 'HourlyForecast.i2m')
GZ_FILE = os.path.join(TEMP_PATH, 'HourlyForecast.gz')

def get_locations():
    locations = MPC.getPrimaryLocations() + MPC.getMetroCities()
    return [(LFR.getCoopId(loc), LFR.getZip(loc)) for loc in locations]

async def fetch_forecast(session, tecci, zip_code):
    log.debug(f'Fetching data for location ID {tecci} (ZIP: {zip_code})')
    url = f'https://api.weather.com/v1/location/{zip_code}:4:US/forecast/hourly/360hour.xml?language=en-US&units=e&apiKey={API_KEY}'

    try:
        async with session.get(url) as response:
            if response.status != 200:
                log.warning(f"Failed to fetch data for {tecci}: HTTP {response.status}")
                return None
            raw = await response.text()
            body = raw[48:-11]  # Trims start/end of XML payload
            return (
                f'<HourlyForecast id="000000000" locationKey="{tecci}" isWxscan="0">'
                f'{body}<clientKey>{tecci}</clientKey></HourlyForecast>'
            )
    except Exception as e:
        log.error(f"Error fetching forecast for {tecci}: {e}")
        return None

async def make_data_file():
    os.makedirs(TEMP_PATH, exist_ok=True)

    log.info("Creating HourlyForecast record")
    header = '<Data type="HourlyForecast">'
    footer = '</Data>'

    async with aiofiles.open(I2M_FILE, 'w') as f:
        await f.write(header)

    async with aiohttp.ClientSession() as session:
        for tecci, zip_code in get_locations():
            xml_block = await fetch_forecast(session, tecci, zip_code)
            if xml_block:
                async with aiofiles.open(I2M_FILE, 'a') as f:
                    await f.write(xml_block)

    async with aiofiles.open(I2M_FILE, 'a') as f:
        await f.write(footer)

    # Pretty print XML
    dom = xml.dom.minidom.parse(I2M_FILE)
    pretty_xml = dom.toprettyxml(indent="  ")
    async with aiofiles.open(I2M_FILE, "w") as f:
        await f.write(pretty_xml[23:])  # Remove XML declaration

    # Gzip compress
    with open(I2M_FILE, 'rb') as f_in, gzip.open(GZ_FILE, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)

    log.info("Compressed XML data into gzip format")

    # Send via BIT
    command = (
        '<MSG>'
        f'<Exec workRequest="storeData(File={GZ_FILE},QGROUP=__HourlyForecast__,Feed=HourlyForecast)" />'
        '<GzipCompressedMsg fname="HourlyForecast" />'
        '</MSG>'
    )
    bit.sendFile([GZ_FILE], [command], 1, 0)

    # Clean up
    os.remove(I2M_FILE)
    os.remove(GZ_FILE)
    log.info("Temporary files cleaned up")

# Entry point
if __name__ == "__main__":
    asyncio.run(make_data_file())
