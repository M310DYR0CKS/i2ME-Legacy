import os
import json
import py2Lib.bit as bit
from datetime import datetime, timedelta
from time import sleep
from random import choice

# Background definitions
BGCatastrophic = ['3094', '3095', '3103', '3115']
BGStorm = []
BGAlert = ['3094', '3095', '3103', '3115']
BGNorm = ['3091', '3092', '3102', '3114']

# Configuration mappings
LDL_OPTIONS = {
    '1': {'name': 'Azul LDL', 'flavor': 'domestic/AzulLDL_16_i2jr'},
    '2': {'name': 'Nemo LDL', 'flavor': 'domestic/ldlE'},
    '3': {'name': 'Enhanced LDL Longform', 'flavor': 'domestic/ldll'},
    '4': {'name': 'Enhanced LDL', 'flavor': 'domestic/ldlC'},
    '5': {'name': 'Enhanced LDL LOT8s', 'flavor': 'domestic/z'}
}

LOT8S_OPTIONS = {
    '1': {'name': 'Azul LOT8s', 'flavor': 'domestic/Azul_i2jr', 'duration': '65'},
    '2': {'name': 'Nemo LOT8s', 'flavor': 'domestic/N', 'duration': '65'},
    '3': {'name': 'Enhanced LOT8s', 'flavor': 'domestic/V', 'duration': '65'},
    '4': {'name': 'Enhanced LOT8s No Intro', 'flavor': 'domestic/U', 'duration': '65'}
}

def display_splash():
    """splash screen"""
    splash = """
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
    print(splash)
    sleep(0)

def display_menu():
    """Load or prompt for configuration"""
    config_path = "lot8s.json"
    
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            print("\n[Auto Load] Configuration loaded from lot8s.json.")
            return config["ldl_config"], config["lot8s_config"]
    
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 17 + "Auto Local On The 8s Scheduler Configuration " + " " * 16 + "║")
    print("║" + " " * 20 + "This will handle cueing for you." + "    " * 5 + "      ║")
    print("║" + " " * 26 + "Created by the 9D Crew." + " " * 25 + "    ║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # LDL Selection
    print("┌─ Select LDL Style ─────────────────────────────────────────────────────────┐")
    for key, value in LDL_OPTIONS.items():
        print(f"│ {key}. {value['name']:<73} │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    
    while True:
        ldl_choice = input("\n Enter LDL choice (1-5): ").strip()
        if ldl_choice in LDL_OPTIONS:
            selected_ldl = LDL_OPTIONS[ldl_choice]
            break
        print(" Invalid choice. Please enter 1-5.")
    
    # LOT8s Selection
    print(f"\n Selected LDL: {selected_ldl['name']}")
    print()
    print("┌─ Select LOT8s Flavor ──────────────────────────────────────────────────────┐")
    for key, value in LOT8S_OPTIONS.items():
        print(f"│ {key}. {value['name']:<73} │")
    print("└────────────────────────────────────────────────────────────────────────────┘")
    
    while True:
        lot8s_choice = input("\n Enter LOT8s choice (1-4): ").strip()
        if lot8s_choice in LOT8S_OPTIONS:
            selected_lot8s = LOT8S_OPTIONS[lot8s_choice]
            break
        print(" Invalid choice. Please enter 1-4.")
    
    print(f"\n Selected LOT8s: {selected_lot8s['name']}")
    print(f" Selected LDL: {selected_ldl['name']}")
    print("\n Configuration complete!")
    input("Press Enter to start scheduler...")

    # Save config
    with open(config_path, "w") as f:
        json.dump({
            "ldl_config": selected_ldl,
            "lot8s_config": selected_lot8s
        }, f, indent=4)
        print(f"\n[Saved] Configuration written to {config_path}.")

    return selected_ldl, selected_lot8s

def start_ldl(ldl_config):
    """Start the LDL presentation"""
    Id = ''.join(choice('ABCDEF0123456789') for _ in range(16))
    command = f'<MSG><Exec workRequest="loadPres(File=0,Flavor={ldl_config["flavor"]},Duration=72000,PresentationId=LDL)" /></MSG>'
    bit.sendCommand([command], 1)
    sleep(2)
    
    nowUTC = datetime.utcnow()
    runTime = nowUTC + timedelta(seconds=5)
    ldlRunTime = runTime.strftime('%m/%d/%Y %H:%M:%S:00')
    
    run_command = f'<MSG><Exec workRequest="runPres(File=0,PresentationId=LDL,StartTime={ldlRunTime})" /></MSG>'
    bit.sendCommand([run_command], 1)
    print(f"Started LDL: {ldl_config['name']}")

def runLo8s(lot8s_config, ldl_config, logo=None, EmergencyLFCancel=0):
    """Run Local on the 8s with selected configurations"""
    Id = ''.join(choice('ABCDEF0123456789') for _ in range(16))
    nowUTC = datetime.utcnow()
    now = datetime.now()
    
    runTime = nowUTC + timedelta(seconds=30)
    friendlyLo8sRunTime = (now + timedelta(seconds=30)).strftime('%I:%M:%S %p')
    ldlCancelTime = runTime.strftime('%m/%d/%Y %H:%M:%S:02')
    lo8sRunTime = runTime.strftime('%m/%d/%Y %H:%M:%S:00')
    
    duration_seconds = int(lot8s_config['duration'])
    nextLDLRunTime = runTime + timedelta(seconds=duration_seconds + 26)
    nextLDLRun = nextLDLRunTime.strftime('%m/%d/%Y %H:%M:%S:02')
    
    duration_map = {'60': '1800', '65': '1950', '90': '2700', '120': '3600'}
    duration = duration_map.get(lot8s_config['duration'], '1950')
    
    if EmergencyLFCancel:
        print(f'[KILL SWITCH] No LOT8s will air. Triggered at {friendlyLo8sRunTime}')
        sleep(27)
    else:
        print(f'Preparing LOT8s ({lot8s_config["name"]}) at {friendlyLo8sRunTime}...')
        command = f'<MSG><Exec workRequest="loadPres(File=0,VideoBehind=000,Flavor={lot8s_config["flavor"]},Duration={duration},PresentationId={Id}'
        if logo:
            command += f',Logo=domesticAds/TAG{logo}'
        command += ')" /></MSG>'
        bit.sendCommand([command], 1)
        sleep(27)
    
    print('Canceling LDL...')
    bit.sendCommand([f'<MSG><Exec workRequest="cancelPres(File=0,PresentationId=LDL,StartTime={ldlCancelTime})" /></MSG>'], 1)
    
    if not EmergencyLFCancel:
        print('Running LOT8s...')
        bit.sendCommand([f'<MSG><Exec workRequest="runPres(File=0,PresentationId={Id},StartTime={lo8sRunTime})" /></MSG>'], 1)
        sleep(duration_seconds - 5)
    
    if EmergencyLFCancel:
        print('Reactivating LDL post-emergency...')
    else:
        print(f'Preparing next LDL ({ldl_config["name"]})...')
    
    ldl_id = ''.join(choice('ABCDEF0123456789') for _ in range(16))
    bit.sendCommand([f'<MSG><Exec workRequest="loadPres(File=0,Flavor={ldl_config["flavor"]},Duration=72000,PresentationId=LDL)" /></MSG>'], 1)
    sleep(10)
    bit.sendCommand([f'<MSG><Exec workRequest="runPres(File=0,PresentationId=LDL,StartTime={nextLDLRun})" /></MSG>'], 1)
    print(f'Next LDL ({ldl_config["name"]}) scheduled for {nextLDLRun}')

def main():
    """Main scheduler loop"""
    display_splash()
    ldl_config, lot8s_config = display_menu()
    EmergencyLFCancel = 0
    
    print('\n' + '╔' + '═' * 58 + '╗')
    print('║' + ' ' * 10 + 'Auto Local On The 8s Scheduler Started' + ' ' * 10 + '║')
    print('║' + f' LDL Style: {ldl_config["name"]}'.ljust(56) + ' ║')
    print('║' + f' LOT8s Flavor: {lot8s_config["name"]}'.ljust(56) + ' ║')
    print('║' + ' Press Ctrl+C to stop.'.ljust(56) + ' ║')
    print('╚' + '═' * 58 + '╝')
    
    start_ldl(ldl_config)
    
    while True:
        now = datetime.now()
        minute = now.minute
        second = now.second
        
        if minute % 10 == 7 and second == 30:
            print(f"\n[{now.strftime('%I:%M:%S %p')}] Preparing for LOT8s in 30 seconds...")
            logo = choice(BGNorm) if BGNorm else None
            runLo8s(lot8s_config, ldl_config, logo, EmergencyLFCancel)
            sleep(60)
        else:
            sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nScheduler Stopped. Goodbye!\n')
