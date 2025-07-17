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

tecciId = []
zipCodes = []

# Auto-grab the tecci and zip codes
for i in MPC.getPrimaryLocations():
    tecciId.append(LFR.getCoopId(i))
    zipCodes.append(LFR.getZip(i))

# Grab metro map city tecci and zip codes
for i in MPC.getMetroCities():
    tecciId.append(LFR.getCoopId(i))
    zipCodes.append(LFR.getZip(i))

apiKey = '8de2d8b3a93542c9a2d8b3a935a2c909'

async def getData(tecci, zipCode):
    fetchUrl = 'https://api.weather.com/v1/location/' + zipCode + ':4:US/forecast/daily/7day.xml?language=en-US&units=e&apiKey=' + apiKey
    data = ""

    async with aiohttp.ClientSession() as s: 
        async with s.get(fetchUrl) as r:
            data = await r.text()

    newData = data[61:-24]
    
    l.debug('Gathering data for location id ' + tecci)
    #Write to .i2m file
    i2Doc = '<DailyForecast id="000000000" locationKey="' + str(tecci) + '" isWxscan="0">' + '' + newData + '<clientKey>' + str(tecci) + '</clientKey></DailyForecast>'

    async with aiofiles.open('./.temp/DailyForecast.i2m', 'a') as f:
        await f.write(i2Doc)
        await f.close()


async def makeDataFile():
    loop = asyncio.get_running_loop()
    l.info("Writing a DailyForecast record.")
    header = '<Data type="DailyForecast">'
    footer = '</Data>'

    async with aiofiles.open("./.temp/DailyForecast.i2m", 'w') as doc:
        await doc.write(header)

    for x, y in zip(tecciId, zipCodes):
        await getData(x, y)
        
    async with aiofiles.open("./.temp/DailyForecast.i2m", 'a') as end:
        await end.write(footer)


    dom = xml.dom.minidom.parse("./.temp/DailyForecast.i2m")
    pretty_xml_as_string = dom.toprettyxml(indent = "  ")

    async with aiofiles.open("./.temp/DailyForecast.i2m", "w") as g:
        await g.write(pretty_xml_as_string[23:])
        await g.close()

    files = []
    commands = []
    with open("./.temp/DailyForecast.i2m", 'rb') as f_in:
        with gzip.open("./.temp/DailyForecast.gz", 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    gZipFile = "./.temp/DailyForecast.gz"

    files.append(gZipFile)
    command = commands.append('<MSG><Exec workRequest="storeData(File={0},QGROUP=__DailyForecast__,Feed=DailyForecast)" /><GzipCompressedMsg fname="DailyForecast" /></MSG>')
    numFiles = len(files)

    bit.sendFile(files, commands, numFiles, 0)

    os.remove("./.temp/DailyForecast.i2m")
    os.remove("./.temp/DailyForecast.gz")
