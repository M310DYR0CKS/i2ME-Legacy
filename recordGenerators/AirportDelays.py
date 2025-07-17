import requests
import gzip
import os
import shutil
import xml.dom.minidom
import logging, coloredlogs
import aiohttp, aiofiles, asyncio
import sys

# Append custom paths
sys.path.append("./py2lib")
sys.path.append("./Util")
sys.path.append("./records")

# Custom imports
import bit
import MachineProductCfg as MPC
import LFRecord as LFR

# Logging setup
l = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG')

# Config
apiKey = '8de2d8b3a93542c9a2d8b3a935a2c909'
airports = MPC.getAirportCodes()

TEMP_DIR = "./.temp"
DELAY_FILE = f"{TEMP_DIR}/AirportDelays.i2m"
DELAY_GZ = f"{TEMP_DIR}/AirportDelays.gz"

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

async def get_delay_data(airport):
    url = f"https://api.weather.com/v1/airportcode/{airport}/airport/delays.xml?language=en-US&apiKey={apiKey}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    l.debug(f"[{airport}] No delay data or error (status {response.status})")
                    return None
                raw = await response.text()
                trimmed = raw[48:-11].replace('¿', '-')
                return f'<AirportDelays id="000000000" locationKey="{airport}" isWxScan="0">{trimmed}<clientKey>{airport}</clientKey></AirportDelays>'
    except Exception as e:
        l.error(f"Failed to fetch delay for {airport}: {e}")
        return None

async def write_airport_delays():
    l.info("Checking airports for delay data...")
    delay_entries = []

    for airport in airports:
        entry = await get_delay_data(airport)
        if entry:
            delay_entries.append(entry)

    if not delay_entries:
        l.info("No airport delays found.")
        return

    # Write the XML structure
    l.info(f"Writing {len(delay_entries)} airport delay records...")
    async with aiofiles.open(DELAY_FILE, 'w') as f:
        await f.write('<Data type="AirportDelays">\n')
        for entry in delay_entries:
            await f.write(entry + "\n")
        await f.write('</Data>\n')

    # Prettify XML
    dom = xml.dom.minidom.parse(DELAY_FILE)
    prettyXml = dom.toprettyxml(indent="  ")

    async with aiofiles.open(DELAY_FILE, 'w') as f:
        await f.write(prettyXml)

    # Compress
    with open(DELAY_FILE, 'rb') as f_in:
        with gzip.open(DELAY_GZ, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Send to i2 system
    command = '<MSG><Exec workRequest="storeData(File={0},QGROUP=__AirportDelays__,Feed=AirportDelays)" /><GzipCompressedMsg fname="AirportDelays" /></MSG>'
    bit.sendFile([DELAY_GZ], [command], 1, 0)

    # Cleanup
    os.remove(DELAY_FILE)
    os.remove(DELAY_GZ)
    l.info("Airport delay data sent and cleaned up.")

if __name__ == "__main__":
    asyncio.run(write_airport_delays())
