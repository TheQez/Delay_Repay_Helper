# Delay_Repay_Helper
A tool to identify delayed trains and collate information needed to submit a delay repay claim.

This program currently uses the National Rail HSP API to identify the delayed services for a journey, and (soon) will identify which company to apply to for Delay Repay and provide links.

To use this you must sign up to the National Rail Darwin API and create an 'auth.txt' file in the same location of the script, containing your email on the first line and your password on the second.

Note: This program currently displays some delays that did not happen due to limitations in the HSP data when trains do not stop at some stations.

The 'contimes.json' file contains the minimum connection times for most stations in the UK, scraped from brtimes.com using the 'scraper.py' tool written with selenium. As the minimum connection times are unlikely to change there is probably little point in updating them with this script. If you do please be polite and don't cause unnecessary strain on the website.

The 'atocfixed.json' file contains the ATOC fixed link times between stations, taken from the ATOC website and converted to json form using the 'fixedRouteProcessor.py' tool. This includes London tube connections among others.
