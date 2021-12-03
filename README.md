# Delay_Repay_Helper
A tool to identify delayed trains and collate information needed to submit a delay repay claim.

This program currently uses the National Rail HSP API to identify the delayed services for a journey, and (soon) will identify which company to apply to for Delay Repay and provide links.

Note: This program currently displays some delays that did not happen due to limitations in the HSP data when trains do not stop at some stations. It also does not currently have data for tube journeys in London.

The 'contimes.json' file contains the minimum connection times for most stations in the UK, scraped from brtimes.com using the 'scraper.py' tool written with selenium. As the minimum connection times are unlikely to change there is probably little point in updating them with this script.
