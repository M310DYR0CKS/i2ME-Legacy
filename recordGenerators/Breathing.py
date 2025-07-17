import requests
import sys
import gzip
import uuid
import os
import shutil
import xml.dom.minidom
import logging,coloredlogs
import aiohttp, aiofiles, asyncio

sys.path.append("./py2lib")
sys.path.append("./Util")
sys.path.append("./records")
import bit
import MachineProductCfg as MPC
import LFRecord as LFR

l = logging.getLogger(__name__)
coloredlogs.install()

coopIds = []
geocodes = []


# Auto-grab the tecci and zip codes
for i in MPC.getPrimaryLocations():
    coopIds.append(LFR.getCoopId(i))
    geocodes.append(LFR.getLatLong(i).replace('/', ','))

l.debug(coopIds, geocodes)

apiKey = '8de2d8b3a93542c9a2d8b3a935a2c909'

async def getData(coopId, geocode):
    fetchUrl = f"https://api.weather.com/v2/indices/breathing/daypart/7day?geocode={geocode}&language=en-US&format=xml&apiKey={apiKey}"
    data = ""

    #Fetch data
    async with aiohttp.ClientSession() as s:
        async with s.get(fetchUrl) as r:
            data = await r.text()

    newData = data[63:-26]
    
    l.debug('Gathering data for location id ' + coopId)
    #Write to .i2m file
    i2Doc = '<Breathing id="000000000" locationKey="' + str(coopId) + '" isWxscan="0">' + '' + newData + '<clientKey>' + str(coopId) + '</clientKey></Breathing>'

    async with aiofiles.open("./.temp/Breathing.i2m", "a") as f:
        await f.write(i2Doc)
        await f.close()


async def makeDataFile():
    loop = asyncio.get_running_loop()
    l.info("Writing a Breathing forecast record.")
    header = '<Data type="Breathing">'
    footer = '</Data>'

    async with aiofiles.open("./.temp/Breathing.i2m", 'w') as doc:
        await doc.write(header)

    for x, y in zip(coopIds, geocodes):
        await getData(x, y)
        
    async with aiofiles.open("./.temp/Breathing.i2m", 'a') as end:
        await end.write(footer)


    dom = xml.dom.minidom.parse("./.temp/Breathing.i2m")
    pretty_xml_as_string = dom.toprettyxml(indent = "  ")

    async with aiofiles.open("./.temp/Breathing.i2m", "w") as g:
        await g.write(pretty_xml_as_string[23:])
        await g.close()

    files = []
    commands = []
    with open("./.temp/Breathing.i2m", 'rb') as f_in:
        with gzip.open("./.temp/Breathing.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    gZipFile = "./.temp/Breathing.gz"

    files.append(gZipFile)
    command = commands.append('<MSG><Exec workRequest="storeData(File={0},QGROUP=__Breathing__,Feed=Breathing)" /><GzipCompressedMsg fname="Breathing" /></MSG>')
    numFiles = len(files)

    bit.sendFile(files, commands, numFiles, 0)

    os.remove("./.temp/Breathing.i2m")
    os.remove("./.temp/Breathing.gz")
