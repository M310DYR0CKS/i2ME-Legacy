<h1 align="center"><strong>IntelliStar 2 Data Collector</strong></h1>

# NOTICE FOR THIS REPOSITORY
This is an unmaintained version of the legacy IntelliStar 2 Data Collector developed when I was originally working with the OpenTelecom group. All git commit history has remained intact, and this software is free to use and modify so long as a closed-source version is not distributed, per the GNU Public License. 

Enjoy!

# Requirements
* Properly set up interface for UDP.
* [Python 3.8.0](https://www.python.org/downloads/release/python-380/)

## Completed Records
- [X] Aches and Pains
- [X] Air Quality
- [X] Airport Delays + National Airport delays
- [X] Alerts *(BERecord)*
- [X] Breathing
- [X] Current Conditions
- [X] Daily Forecasts
- [X] Hourly Forecasts
- [X] Heating and Cooling
- [X] Mosquito Activity
- [X] Pollen Forecasts
- [X] Tide Station Forecasts
- [X] Watering Needs
- [ ] Marine Forecasts
- [ ] Traffic Forecasts **(API access missing)**

# Usage instructions
1) Ensure that [Python 3.8 is installed](https://www.python.org/downloads/release/python-380/).
2) [Download a release](https://github.com/Open-Telecom/i2MessageEncoder-Rewrite/releases/tag/v2.0.2), and unzip to the wanted directory.
3) Use command prompt to enter the directory of the scripts, then install package requirements:<br/>
```py -3 -m pip install -r requirements.txt``` <br/>
4) Drop your unit's **MachineProductConfiguration.xml** file into the root of the script
5) Run ``main.py``

### Attributions & Disclaimers
Air Quality reports are powered by Copernicus Atmosphere Monitoring Service Information 2022.
Neither the European Commission nor ECMWF is responsible for any use that may be made of the Copernicus Information or Data it contains.

### I will fix the bugs but dont think i will offer support of none that shit fuck the TWC Community :3
