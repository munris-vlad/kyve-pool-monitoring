#!/usr/bin/env python3
import os, requests
import configparser
import json
import datetime

class Monitoring():
    def __init__(self, config_file='config.ini'):
        self.read_config(config_file)
        now = datetime.datetime.now()
        validator_data = self.get_validator_data()
        self.check_pools(validator_data)
        if (self.telegram_chat_info_id != None and now.minute == 1):
            self.check_stats(validator_data)


    def check_stats(self, validator_data):
        self.send_validator_stat(
            validator_data['metadata']['moniker'],
            str(self.shares_to_decimal(validator_data['total_delegation'])) + self.ticker,
            str(self.shares_to_decimal(validator_data['self_delegation'])) + self.ticker
        )

    def check_pools(self, validator_data):
        for pool in validator_data['pools']:
            if self.shares_to_decimal(pool['balance']) < self.funds_alert:
                self.send_validator_alert(
                    "FUNDS ALERT",
                    validator_data['metadata']['moniker'],
                    pool['pool']['name'],
                    'Balance',
                    str(self.shares_to_decimal(pool['balance'])) + self.ticker
                )

            if (pool['pool']['status'] != 'POOL_STATUS_ACTIVE'):
                self.send_validator_alert(
                    "STATUS ALERT",
                    validator_data['metadata']['moniker'],
                    pool['pool']['name'],
                    'Status ',
                    pool['pool']['status']
                )

            if (int(pool['points']) > 0):
                self.send_validator_alert(
                    "POINTS ALERT",
                    validator_data['metadata']['moniker'],
                    pool['pool']['name'],
                    'Points ',
                    pool['points']
                )

    def get_validator_data(self):
        r = requests.get(self.api_url + '/kyve/query/v1beta1/staker/' + self.valoper)
        data = json.loads(r.content)
        return data['staker']

    def read_config(self, config_file):
        config = configparser.ConfigParser()
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            print( f"Configuration File Does Not Exist: { config_file }")

        if "API_URL" in config['VARIABLES']:
            self.api_url = config['VARIABLES']['API_URL']
        else:
            self.api_url = None

        if "VALOPER" in config['VARIABLES']:
            self.valoper = config['VARIABLES']['VALOPER']
        else:
            self.valoper = None

        if "TOKEN_FUNDS_ALERT" in config['VARIABLES']:
            self.funds_alert = int(config['VARIABLES']['TOKEN_FUNDS_ALERT'])
        else:
            self.funds_alert = None

        if "TELEGRAM_TOKEN" in config['VARIABLES']:
            self.telegram_token = config['VARIABLES']['TELEGRAM_TOKEN']
        else:
            self.telegram_token = None

        if "TELEGRAM_CHAT_ALERT_ID" in config['VARIABLES']:
            self.telegram_chat_alert_id = config['VARIABLES']['TELEGRAM_CHAT_ALERT_ID']
        else:
            self.telegram_chat_alert_id = None

        if "TELEGRAM_CHAT_INFO_ID" in config['VARIABLES']:
            self.telegram_chat_info_id = config['VARIABLES']['TELEGRAM_CHAT_INFO_ID']
        else:
            self.telegram_chat_info_id = None

        self.decimals = 1000000000
        self.ticker = "$KYVE"
        self.config = config

    def send(self, msg, type = 'alert'):
        if self.telegram_token != None and self.telegram_chat_alert_id != None:
            if (type == 'alert'):
                requests.post(f'https://api.telegram.org/bot{self.telegram_token}/sendMessage?chat_id={self.telegram_chat_alert_id}&text={msg}&parse_mode=HTML')
            else:
                requests.post(f'https://api.telegram.org/bot{self.telegram_token}/sendMessage?chat_id={self.telegram_chat_info_id}&text={msg}&parse_mode=HTML')

    def send_validator_alert(self, alert, moniker, pool, field, value):
        self.send(f"<b>{alert}</b> \n<code>Validator .. {moniker} \nPool ....... {pool} \n{field} .... {value}</code>")

    def send_validator_stat(self, moniker, total_delegation, self_delegation):
        self.send(f"<b>{moniker}</b> \n<code>Deletegation total / self .. {total_delegation} / {self_delegation}\n</code>", 'info')

    def shares_to_decimal(self, shares):
        return round(float( shares ) * (1/self.decimals), 2)

    def decimal_to_shares(self, amount):
        return int( amount * self.decimals )

monitoring = Monitoring()