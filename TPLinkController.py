import yaml
import json
import asyncio
import time
from aioudp import *
from TPLinkInstance import *
from DataSource import *
from HASSWebSocketController import HASSWebSocketController


# Check if a multi-layer key exists
def keys_exist(element, *keys):
    if not isinstance(element, dict):
        raise AttributeError('keys_exists() expects dict as first argument.')
    if len(keys) == 0:
        raise AttributeError('keys_exists() expects at least two arguments, one given.')

    _element = element
    for key in keys:
        try:
            _element = _element[key]
        except KeyError:
            return False
    return True


class TPLinkController:
    remote_ep = None
    local_ep = None
    instances = []
    hass_sources = []

    def __init__(self, config, port=9999):
        self.config = config
        self.port = port
        self.server_task = None

    def create_instances(self):
        config = yaml.load(self.config, Loader=yaml.FullLoader)
        logging.debug(f"Configuration loaded: {config}")
        sources = config.get('sources')
        print(sources)
        for source in sources.keys():
            # Static value plugs
            if source.lower() == "static":
                # Static sources require no extra config
                static = config['sources'][source]
                # Generate plug instances
                plugs = static['plugs']
                instances = TPLinkInstance.configure_plugs(plugs, DataSource)
                self.instances.extend(instances)

            # HomeAssistant Plugs, using Websockets datasource
            if source.lower() == "hass":
                # Configure this HASS Data source
                hass = config['sources'][source]
                url = hass['url']
                auth_token = hass['auth_token']
                ds_controller = HASSWebSocketController(url, auth_token)

                # Generate plug instances
                plugs = hass['plugs']
                instances = TPLinkInstance.configure_plugs(plugs, HASSSource, ds_controller)

                # Add instances to self
                self.instances.extend(instances)

                # Start controller
                ds_controller.connect()

    def print_instance_wattages(self):
        for inst in self.instances:
            print(f"Inst Power: {inst.power}")

    async def start(self):
        self.create_instances()
        await self._serve()

    async def _serve(self):
        server_start = time()
        logging.info("Starting UDP server")
        self.local_ep = await open_local_endpoint('0.0.0.0', self.port)

        while True:
            print("yes")
            data, addr = await self.local_ep.receive()
            request_addr = addr[0]
            decrypted_data = decrypt(data)

            try:
                json_data = json.loads(decrypted_data)
                # Sense requests the emeter and system parameters
                if keys_exist(json_data, "emeter", "get_realtime") and keys_exist(json_data, "system", "get_sysinfo"):
                    logging.debug("Broadcast received from: %s: %s", request_addr, json_data)

                    if self.remote_ep is None:
                        self.remote_ep = await open_remote_endpoint(request_addr, self.port)

                    # Build and send responses
                    for inst in self.instances:
                        if inst.start_time is None:
                            inst.start_time = server_start
                        # Build response
                        response = inst.generate_response()
                        # Send response
                        logging.debug("Sending response: %s", response)
                        json_str = json.dumps(response, separators=(',', ':'))
                        encrypted_str = encrypt(json_str)
                        # Strip leading 4 bytes for...some reason
                        trun_str = encrypted_str[4:]

                        # self.remote_ep.send(trun_str)
                else:
                    logging.info(f"Unexpected/unhandled message: {json_data}")

            # Appears to not be JSON
            except ValueError as e:
                logging.debug("Did not receive valid json")
                return True

