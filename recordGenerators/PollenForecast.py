import requests
import sys
import gzip
import uuid
import os
import shutil
import xml.dom.minidom
import logging, coloredlogs
import aiohttp, aiofiles, asyncio

sys.path.append("./py2lib")
sys.path.append("./Util")
sys.path.append("./records")
import bit
import MachineProductCfg as MPC
import LFRecord as LFR


l = logging.getLogger(__name__)
coloredlogs.install()

pollenIds = []
geocodes = []


# Auto-grab the tecci and zip codes
for i in MPC.getPrimaryLocations():
    pollenIds.append(LFR.getPollenInfo(i))
    geocodes.append(LFR.getLatLong(i).replace('/', ','))

l.debug(pollenIds, geocodes)

apiKey = '8de2d8b3a93542c9a2d8b3a935a2c909'

async def getData(pollenId, geocode):
    fetchUrl = f"https://api.weather.com/v2/indices/pollen/daypart/7day?geocode={geocode}&language=en-US&format=xml&apiKey={apiKey}"
    data = ""
    #Fetch data
    async with aiohttp.ClientSession() as s:
        async with s.get(fetchUrl) as r:
            data = await r.text()

    newData = data[63:-26]
    
    l.debug('Gathering data for location id ' + pollenId)
    #Write to .i2m file
    i2Doc = '<PollenForecast id="000000000" locationKey="' + str(pollenId) + '" isWxscan="0">' + '' + newData + '<clientKey>' + str(pollenId) + '</clientKey></PollenForecast>'

    async with aiofiles.open("./.temp/PollenForecast.i2m", "a") as f:
        await f.write(i2Doc)
        await f.close()


async def makeDataFile():
    loop = asyncio.get_running_loop()
    l.info("Writing a PollenForecast record.")
    header = '<Data type="PollenForecast">'
    footer = '</Data>'

    async with aiofiles.open("./.temp/PollenForecast.i2m", 'w') as doc:
        await doc.write(header)

    for x, y in zip(pollenIds, geocodes):
        await getData(x, y)
        
    async with aiofiles.open("./.temp/PollenForecast.i2m", 'a') as end:
        await end.write(footer)


    dom = xml.dom.minidom.parse("./.temp/PollenForecast.i2m")
    pretty_xml_as_string = dom.toprettyxml(indent = "  ")

    async with aiofiles.open("./.temp/PollenForecast.i2m", "w") as g:
        await g.write(pretty_xml_as_string[23:])
        await g.close()

    files = []
    commands = []
    with open("./.temp/PollenForecast.i2m", 'rb') as f_in:
        with gzip.open("./.temp/PollenForecast.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    gZipFile = "./.temp/PollenForecast.gz"

    files.append(gZipFile)
    command = commands.append('<MSG><Exec workRequest="storeData(File={0},QGROUP=__PollenForecast__,Feed=PollenForecast)" /><GzipCompressedMsg fname="PollenForecast" /></MSG>')
    numFiles = len(files)

    bit.sendFile(files, commands, numFiles, 0)

    os.remove("./.temp/PollenForecast.i2m")
    os.remove("./.temp/PollenForecast.gz")
