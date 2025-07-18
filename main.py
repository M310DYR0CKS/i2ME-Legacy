import asyncio, aiofiles
from asyncio.log import logger
from asyncore import loop
import logging,coloredlogs
from radar import TWCRadarCollector
import os
from datetime import datetime
import RecordTasks

l = logging.getLogger(__name__)
coloredlogs.install(logger=l)

useRadarServer = True

l.info("Starting i2RecordCollector")
l.info("Developed by mewtek32, Floppaa, Goldblaze, and needlenose")

async def createTemp():
    """ Used on a first time run, creates necessary files & directories for the message encoder to work properly. """
    if not (os.path.exists('./.temp/')):
        l.info("Creating necessary directories & files..")
        os.mkdir('./.temp')
        
        # Used for the record generator
        os.mkdir('./.temp/tiles/')
        os.mkdir('./.temp/tiles/output/')


        os.mkdir('./.temp/output')


        # Create msgId file for bit.py
        async with aiofiles.open('./.temp/msgId.txt', 'w') as msgId:
            await msgId.write('410080515')
            await msgId.close()
    else:
        l.debug(".temp file exists")
        return


async def main():
    await createTemp()

    mosaicTask = asyncio.create_task(RecordTasks.updateMosaicTask())
    satradTask = asyncio.create_task(RecordTasks.updateSatradTask())
    alertsTask = asyncio.create_task(RecordTasks.alertsTask())
    coTask = asyncio.create_task(RecordTasks.coTask())
    hfTask = asyncio.create_task(RecordTasks.hfTask())
    dfTask = asyncio.create_task(RecordTasks.dfTask())
    aqTask = asyncio.create_task(RecordTasks.aqTask())
    aptTask = asyncio.create_task(RecordTasks.aptTask())
    apTask = asyncio.create_task(RecordTasks.apTask())
    brTask = asyncio.create_task(RecordTasks.brTask())
    hcTask = asyncio.create_task(RecordTasks.hcTask())
    maTask = asyncio.create_task(RecordTasks.maTask())
    pTask = asyncio.create_task(RecordTasks.pTask())
    tTask = asyncio.create_task(RecordTasks.tTask())
    wnTask = asyncio.create_task(RecordTasks.wnTask())

    # In theory, these should all run concurrently without problems
    await alertsTask
    await coTask
    await hfTask
    await dfTask
    await aqTask
    await aptTask
    await apTask
    await brTask
    await hcTask
    await maTask
    await pTask
    await tTask
    await wnTask


if __name__ == "__main__":
    asyncio.run(main())
