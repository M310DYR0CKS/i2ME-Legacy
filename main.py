import asyncio, aiofiles
import logging, coloredlogs
import os
from datetime import datetime

import RecordTasks

# Set up logger
l = logging.getLogger(__name__)
coloredlogs.install(logger=l)

ascii_art = """
         ############                              
     ##################                           
   ######################                         
Ss  ########################                        
 #############  ###########                       
############     ###########                      
############################                      
#############################                     
#############################                     
#############################                     
###########       ###########                     
 ####################################             
  #######################################         
   ########################################       
     ########################################     
         #####################################    
          ##################       ############   
     #    #################         ############  
    #######################          ###########  
    #####################            ###########  
    #####################           ############  
    #####################           ############  
          ###############         #############   
          ####################################    
          ###################################     
          #################################       
           #############################
"""

l.info(ascii_art)
l.info("Starting i2RecordCollector")
l.info("Made for the 9D crew froked from i2ME")

async def createTemp():
    """Creates necessary files & directories for the message encoder to work properly."""
    if not os.path.exists('./.temp/'):
        l.info("Creating necessary directories & files...")
        os.makedirs('./.temp/tiles/output', exist_ok=True)

        async with aiofiles.open('./.temp/msgId.txt', 'w') as msgId:
            await msgId.write('410080515')
    else:
        l.debug(".temp directory already exists")

async def main():
    await createTemp()

    tasks = [
        asyncio.create_task(RecordTasks.alertsTask()),
        asyncio.create_task(RecordTasks.coTask()),
        asyncio.create_task(RecordTasks.hfTask()),
        asyncio.create_task(RecordTasks.dfTask()),
        asyncio.create_task(RecordTasks.aqTask()),
        asyncio.create_task(RecordTasks.aptTask()),
        asyncio.create_task(RecordTasks.apTask()),
        asyncio.create_task(RecordTasks.brTask()),
        asyncio.create_task(RecordTasks.hcTask()),
        asyncio.create_task(RecordTasks.maTask()),
        asyncio.create_task(RecordTasks.pTask()),
        asyncio.create_task(RecordTasks.tTask()),
        asyncio.create_task(RecordTasks.wnTask()),
    ]

    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
