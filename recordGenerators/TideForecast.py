import shutil
import logging,coloredlogs
import datetime
from py2Lib import bit
import Util.MachineProductCfg as MPC
import records.LFRecord as LFR
import gzip
from os import remove
import xml.dom.minidom
import aiohttp, aiofiles, asyncio

l = logging.getLogger(__name__)
coloredlogs.install()

geocodes = []
tideStations = []

for i in MPC.getTideStations():
    tideStations.append(i)
    geocodes.append(LFR.getLatLong(i))

apiKey = "8de2d8b3a93542c9a2d8b3a935a2c909"

async def getData(tideStation, geocode):
    today = datetime.date.today()
    startDate = today.strftime('%Y%m%d')
    endDate_unformatted = datetime.datetime.strptime(startDate, '%Y%m%d') + datetime.timedelta(days=5)
    endDate = endDate_unformatted.strftime('%Y%m%d')
    data = ""

    fetchUrl = f"https://api.weather.com/v1/geocode/{geocode}/forecast/tides.xml?language=en-US&units=e&startDate={startDate}&endDate={endDate}&apiKey={apiKey}"

    async with aiohttp.ClientSession() as s:
        async with s.get(fetchUrl) as r:
            if r.status != 200:
                l.error(f"Failed to write TideForecast -- status code {r.status}")
                return
            
            data = await r.text()


    newData = data[53:-16]

    i2Doc = f'\n  <TidesForecast id="000000000" locationKey="{tideStation}" isWxScan="0">\n    {newData}\n    <clientKey>{tideStation}</clientKey>\n </TidesForecast>'

    async with aiofiles.open('./.temp/TidesForecast.i2m', 'a') as f:
        await f.write(i2Doc)
        await f.close()

async def makeRecord():
    loop = asyncio.get_running_loop()
    if len(tideStations) < 1:
        l.debug("Skipping TidesForecast -- No locations.")
        return

    l.info("Writing TidesForecast record.")

    header = '<Data type="TidesForecast">'
    footer = '</Data>'

    async with aiofiles.open('./.temp/TidesForecast.i2m', 'a') as doc:
        await doc.write(header)

    for (x, y) in zip(tideStations, geocodes):
        await getData(x,y)

    async with aiofiles.open('./.temp/TidesForecast.i2m', 'a') as end:
        await end.write(footer)

    dom = xml.dom.minidom.parse('./.temp/TidesForecast.i2m')
    xmlPretty = dom.toprettyxml(indent= "  ")

    async with aiofiles.open('./.temp/TidesForecast.i2m', 'w') as g:
        await g.write(xmlPretty[23:])
        await g.close()

    
    # Compresss i2m to gzip
    with open ('./.temp/TidesForecast.i2m', 'rb') as f_in:
        with gzip.open('./.temp/TidesForecast.gz', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)

    file = "./.temp/TidesForecast.gz"
    command = '<MSG><Exec workRequest="storeData(File={0},QGROUP=__TidesForecast__,Feed=TidesForecast)" /><GzipCompressedMsg fname="TidesForecast" /></MSG>'

    bit.sendFile([file], [command], 1, 0)

    remove('./.temp/TidesForecast.i2m')
    remove('./.temp/TidesForecast.gz')
