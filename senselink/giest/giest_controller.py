# Copyright 2022, Charles Powell

import logging
import asyncio
from typing import Dict
from contextlib import AsyncExitStack

import requests

GIEST_LOGGER = logging.getLogger('giest')
GIEST_LOGGER.setLevel(logging.WARNING)

class GIESTController:
    data_sources = []
    loop = asyncio.get_event_loop()
    def __init__(self, url,device_id):
        self.url = url
        self.device_id=device_id

    def connect(self):
        logging.info(f"Starting client to URL: {self.url}")
        return self.client_handler()
        # asyncio.ensure_future(self.client_handler())
        # self.loop.run_forever()

    def get_update(self):
        logging.info(f"Starting client to URL: {self.url}")
        response = requests.get(f"{self.url}/api/dev")
        json_res = response.json()

        for ds in self.data_sources:
            ds.parse_bulk_update(json_res['data'][self.device_id]['outlet'][ds.outlet_num])

    async def client_handler(self):
        while True:
            response = requests.get(f"{self.url}/api/dev")
            json_res = response.json()

            for ds in self.data_sources:
                ds.parse_bulk_update(json_res['data'][self.device_id]['outlet'][ds.outlet_num])
            await asyncio.sleep(15)
        
