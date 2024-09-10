import requests
from hydra import compose, initialize
from omegaconf import DictConfig, OmegaConf
from pandas import DataFrame, concat, to_datetime
from hydra.core.global_hydra import GlobalHydra

class ApiReader:
    def __init__(self, config_path: str):
        try:
            initialize(config_path, config_path, version_base=None)
        except ValueError:
            GlobalHydra.instance().clear()
            initialize(config_path, config_path, version_base=None)
        cfg = compose(config_name='conf')

        self.mc_api = cfg.default_values.miningcore_api

    def get_api_data(self, api_url):
        try:
            # Send a GET request to the API
            response = requests.get(api_url)
    
            # Check if the request was successful (status code 200)
            if response.status_code == 200:
                # Parse the response as JSON (assuming the API returns JSON data)
                data = response.json()
                return data
            else:
                print(f"Failed to retrieve data: Status code {response.status_code}")
                return None
    
        except requests.exceptions.RequestException as e:
            # Handle any exceptions that occur during the request
            print(f"An error occurred: {e}")
            return None
            
    def get_pool_stats(self):
        url = '{}/{}'.format(self.mc_api, 'poolstats')
        pool_data = self.get_api_data(url)

        latest_sample = pool_data[-1]
        return latest_sample

    def get_mining_stats(self):
        url = '{}/{}'.format(self.mc_api, 'minerstats')
        miner_data = self.get_api_data(url)
        return miner_data

    def get_block_stats(self):
        url = '{}/{}'.format(self.mc_api, 'blocks')
        blocks = self.get_api_data(url)
        return blocks

    def get_my_blocks(self, address):
        url = '{}/blocks/{}'.format(self.mc_api, address)
        blocks = self.get_api_data(url)
        return blocks

    def get_miner_payment_stats(self, address):
        url = '{}/minerstats/{}'.format(self.sigscore_api, address)
        return self.get_api_data(url)

    def get_live_miner_data(self):
        url = '{}/{}'.format(self.sigscore_api, 'live')
        return self.get_api_data(url)

    def get_my_live_miner_data(self, address):
        url = '{}/live/{}'.format(self.sigscore_api, address)
        return self.get_api_data(url)

    def get_miner_samples(self, address):
        url = '{}/samples/{}'.format(self.sigscore_api, address)
        return self.get_api_data(url)

        

