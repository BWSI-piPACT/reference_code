#!/usr/bin/python3
# -*- mode: python; coding: utf-8 -*-
"""Bluetooth Low Energy (BLE) beacon advertisement and scanning.

Execution of a BLE beacon for use in BWSI PiPact independent project. 
Configuration of beacon done via external YAML. Underlying functionality 
provided by PyBluez module (https://github.com/pybluez/pybluez). Beacon 
uses iBeacon format (https://en.wikipedia.org/wiki/IBeacon).
"""

import argparse
from bluetooth.ble import BeaconService
from datetime import datetime
from itertools import zip_longest
import logging
import logging.config
import pandas as pd
from pathlib import Path
import sys
import time
from uuid import uuid1
import yaml

# Default configuration
LOG_NAME = 'pi_pact.log'
DEFAULT_CONFIG = {
    'advertiser': {
        'control_file': "advertiser_control",
        'timeout': None,
        'uuid': '',
        'major': 1,
        'minor': 1,
        'tx_power': 1,
        'interval': 200
        },
    'scanner': {
        'control_file': "scanner_control",
        'scan_prefix': "pi_pact_scan",
        'timeout': None,
        'revisit': 1,
        'filters': {}
        },
    'logger': {
        'name': LOG_NAME,
        'config': {
            'version': 1,
            'formatters': {
                'full': {
                    'format': '%(asctime)s   %(module)-10s   %(levelname)-8s   %(message)s'},
                'brief': {
                    'format': '%(asctime)s   %(levelname)-8s   %(message)s'},
                },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'brief'
                    },
                'file': {
                    'class': 'logging.handlers.TimedRotatingFileHandler',
                    'level': 'DEBUG',
                    'formatter': 'full',
                    'filename': LOG_NAME,
                    'when': 'H',
                    'interval': 1
                    }
                },
            'loggers': {
                LOG_NAME: {
                    'level': 'DEBUG',
                    'handlers': ['console', 'file']
                    }
                }
            }
        }
    }

# Universal settings
BLE_DEVICE = "hci0"
CONTROL_INTERVAL = 1 # (s)
MAX_TIMEOUT = 600 # (s)
ID_FILTERS = ['ADDRESS', 'UUID', 'MAJOR', 'MINOR', 'TX POWER']
MEASUREMENT_FILTERS = ['TIMESTAMP', 'RSSI']

# Limits
MAJOR_LIMITS = [1, 65535]
MINOR_LIMITS = [1, 65535]
TX_POWER_LIMITS = [-40, 4]
INTERVAL_LIMITS = [20, 10000] # (ms)
ALLOWABLE_FILTERS = ID_FILTERS+MEASUREMENT_FILTERS

class Advertiser(object):
    """Instantiates a BLE beacon advertiser.
    
    Attributes:
        control_file (pathlib.Path): BLE beacon advertiser control file path.
        timeout (float, int): BLE beacon advertiser timeout (s). Must be 
            strictly positive and less than 600.
        uuid (str): BLE beacon advertiser UUID. Must be 32 hexadecimal digits 
            split into 5 groups separated by hyphens. The number of digits in 
            each group from first to last) is {8, 4, 4, 4, 12}.
        major (int): BLE beacon advertiser major value. Must be in [1, 65535].
        minor (int): BLE beacon advertiser minor value. Must be in [1, 65535].
        tx_power (int): BLE beacon advertiser TX power value. Must be in 
            [-40, 4].
        interval (int): BLE beacon advertiser interval (ms) value. Must be in 
            [20, 10000].
    """

    def __init__(self, logger, **kwargs):
        """Instance initialization.

        Args:
            logger (logging.Logger): Configured logger.
            **kwargs: Keyword arguments corresponding to instance attributes. 
                Any unassociated keyword arguments are ignored.
        """
        # Logger
        self.__logger = logger
        # Beacon settings
        for key, value in DEFAULT_CONFIG['advertiser'].items():
            if key in kwargs and kwargs[key]:
                setattr(self, key, kwargs[key])
            else:
                self.__logger.debug("Using default beacon advertiser "
                        f"configuration {key}: {value}.")
                setattr(self, key, value)
        # Create beacon
        self.__service = BeaconService(BLE_DEVICE)
        self.__logger.info("Initialized beacon advertiser.")
        
    def __del__(self):
        """Instance destruction."""
        if self.__control_file_handle is not None:
            self.__control_file_handle.close()
        self.__control_file.unlink()
        
    @property
    def control_file(self):
        """BLE beacon advertiser control file path getter."""
        return self.__control_file
    
    @control_file.setter
    def control_file(self, value):
        """BLE beacon advertiser control file path setter.
        
        Raises:
            TypeError: Beacon advertiser control file must be a string.
        """
        if not isinstance(value, str):
            raise TypeError("Beacon advertiser control file must be a string.")
        else:
            self.__control_file = Path(value).resolve()
            self.__control_file.touch()
            self.__control_file.chmod(0o777)
            with self.__control_file.open(mode='w') as f:
                f.write("0")
            self.__control_file_handle = None
                
    @property
    def timeout(self):
        """BLE beacon advertiser timeout getter."""
        return self.__timeout;
    
    @timeout.setter
    def timeout(self, value):
        """BLE beacon advertiser timeout setter.

        Raises:
            TypeError: Beacon advertiser timeout must be a float, integer, or 
                NoneType.
            ValueError: Beacon advertiser timeout must be strictly positive.
            ValueError: Beacon advertisertimeout cannot exceed maximum 
                allowable timeout.
        """
        if value is not None:
            if not isinstance(value, (float, int)):
                raise TypeError("Beacon advertiser timeout must be a float, "
                        "integer, or NoneType.")
            elif value <= 0:
                raise ValueError("Beacon advertiser timeout must be strictly "
                        "positive.")
            elif value > MAX_TIMEOUT:
                raise ValueError("Beacon advertiser timeout cannot exceed "
                        "maximum allowable timeout.")
        self.__timeout = value
    
    @property
    def uuid(self):
        """BLE beacon advertiser UUID getter."""
        return self.__uuid;

    @uuid.setter
    def uuid(self, value):
        """BLE beacon advertiser UUID setter.

        Raises:
            TypeError: Beacon advertiser UUID must be a string.
        """
        if not isinstance(value, str):
            raise TypeError("Beacon advertiser UUID must be a string.")
        elif not value:
            self.__uuid = str(uuid1())
            self.__logger.debug(f"Beacon advertiser UUID set to {self.__uuid}")
        else:
            self.__uuid = value;

    @property
    def major(self):
        """BLE beacon advertiser major value getter."""
        return self.__major

    @major.setter
    def major(self, value):
        """BLE beacon advertiser major value setter.

        Raises:
            TypeError: Beacon advertiser major value must be an integer.
            ValueError: Beacon advertiser major value must be in [1, 65535].
         """
        if not isinstance(value, int):
            raise TypeError("Beacon advertiser major value must be an integer.")
        elif value < MAJOR_LIMITS[0] or value > MAJOR_LIMITS[1]:
            raise ValueError("Beacon advertiser major value must be in range "
                    f"{MAJOR_LIMITS}.")
        self.__major = value
            
    @property
    def minor(self):
        """BLE beacon advertiser minor value getter."""
        return self.__minor

    @minor.setter
    def minor(self, value):
        """BLE beacon advertiser minor value setter.

        Raises:
            TypeError: Beacon advertiser minor value must be an integer.
            ValueError: Beacon advertiser minor value must be in [1, 65535].
         """
        if not isinstance(value, int):
            raise TypeError("Beacon advertiser minor value must be an integer.")
        elif value < MINOR_LIMITS[0] or value > MINOR_LIMITS[1]:
            raise ValueError("Beacon advertiser minor value must be in range "
                    f"{MINOR_LIMITS}.")
        self.__minor = value

    @property
    def tx_power(self):
        """BLE beacon advertiser TX power value getter."""
        return self.__tx_power

    @tx_power.setter
    def tx_power(self, value):
        """BLE beacon Beacon advertiser TX power setter.

        Raises:
            TypeError: Beacon advertiser TX power must be an integer.
            ValueError: Beacon advertiser TX power must be in [-40, 4].
         """
        if not isinstance(value, int):
            raise TypeError("Beacon advertiser TX power must be an integer.")
        elif value < TX_POWER_LIMITS[0] or value > TX_POWER_LIMITS[1]:
            raise ValueError("Beacon advertiser TX power must be in range "
                    f"{TX_POWER_LIMITS}.")
        self.__tx_power = value

    @property
    def interval(self):
        """BLE beacon advertiser interval getter."""
        return self.__interval

    @interval.setter
    def interval(self, value):
        """BLE beacon advertiser interval setter.

        Raises:
            TypeError: Beacon advertiser interval must be an integer.
            ValueError: Beacon advertiser interval must be in [20, 10000].
         """
        if not isinstance(value, int):
            raise TypeError("Beacon advertiser interval must be an integer.")
        elif value < INTERVAL_LIMITS[0] or value > INTERVAL_LIMITS[1]:
            raise ValueError("Beacon advertiser interval must be in range "
                    f"{INTERVAL_LIMITS}.")
        self.__interval = value
            
    def advertise(self, timeout=0):
        """Execute BLE beacon advertisement.
        
        Args:
            timeout (int, float): Time (s) for which to advertise beacon. If
                specified as None then advertises till user commanded stop via
                control file. Defaults to configuration value.
        """
        # Parse inputs
        if timeout == 0:
            timeout = self.timeout
        # Update control file
        with self.__control_file.open(mode='w') as f:
            f.write("0")
        # Start advertising
        self.__logger.info("Starting beacon advertiser with timeout "
                f"{timeout}.")
        self.__service.start_advertising(self.uuid, self.major, self.minor,
                                         self.tx_power, self.interval)
        # Stop advertising based on either timeout or control file
        start_time = time.monotonic()
        self.__control_file_handle = self.__control_file.open(mode='r+')
        run = True
        while run:
            time.sleep(CONTROL_INTERVAL)
            if timeout is not None:
                if (time.monotonic()-start_time) > timeout:
                    self.__logger.debug("Beacon advertiser timed out.")
                    run = False
            self.__control_file_handle.seek(0)
            control_flag = self.__control_file_handle.read()
            if control_flag != "0":
                self.__logger.debug("Beacon advertiser control flag set to "
                        "stop.")
                run = False
        self.__logger.info("Stopping beacon advertiser.")        
        self.__service.stop_advertising()
        # Cleanup
        self.__control_file_handle.close()
        with self.__control_file.open('w') as f:
            f.write("0")
            
class Scanner(object):
    """Instantiates a BLE beacon scanner.
    
    Attributes:
        control_file (pathlib.Path): BLE beacon scanner control file path.
        timeout (float, int): BLE beacon scanner timeout (s). Must be strictly
            positive and less than 600.
        revisit (int): BLE beacon scanner revisit interval (s). Must be 
            strictly positive.
        filters (dict): Filters to apply to received beacons. Available
            filters/keys are {'address', 'uuid', 'major', 'minor'}.
    """

    def __init__(self, logger, **kwargs):
        """Instance initialization.

        Args:
            logger (logging.Logger): Configured logger.
            **kwargs: Keyword arguments corresponding to instance attributes. 
                Any unassociated keyword arguments are ignored.
        """
        # Logger
        self.__logger = logger
        # Beacon settings
        for key, value in DEFAULT_CONFIG['scanner'].items():
            if key in kwargs and kwargs[key]:
                setattr(self, key, kwargs[key])
            else:
                self.__logger.debug("Using default beacon scanner "
                        f"configuration {key}: {value}.")
                setattr(self, key, value)
        # Create beacon
        self.__service = BeaconService(BLE_DEVICE)
        self.__logger.info("Initialized beacon scanner.")
        
    def __del__(self):
        """Instance destruction."""
        if self.__control_file_handle is not None:
            self.__control_file_handle.close()
        self.__control_file.unlink()
        
    @property
    def control_file(self):
        """BLE beacon scanner control file path getter."""
        return self.__control_file
    
    @control_file.setter
    def control_file(self, value):
        """BLE beacon scanner control file path setter.
        
        Raises:
            TypeError: Beacon scanner control file must be a string.
        """
        if not isinstance(value, str):
            raise TypeError("Beacon scanner control file must be a string.")
        # Initialize control file
        self.__control_file = Path(value).resolve()
        self.__control_file.touch()
        self.__control_file.chmod(0o777)
        with self.__control_file.open(mode='w') as f:
            f.write("0")
        self.__control_file_handle = None

    @property
    def scan_prefix(self):
        """BLE beacon scanner scan file prefix getter."""
        return self.__scan_prefix
    
    @scan_prefix.setter
    def scan_prefix(self, value):
        """BLE beacon scanner scan file prefix setter.
        
        Raises:
            TypeError: Beacon scanner scan file prefix must be a string.
        """
        if not isinstance(value, str):
            raise TypeError("Beacon scanner scan file prefix must be a string.")
        self.__scan_prefix = value
   
    @property
    def timeout(self):
        """BLE beacon scanner timeout getter."""
        return self.__timeout;
    
    @timeout.setter
    def timeout(self, value):
        """BLE beacon scanner timeout setter.

        Raises:
            TypeError: Beacon scanner timeout must be a float, integer, or 
                NoneType.
            ValueError: Beacon scanner timeout must be strictly positive.
            ValueError: Beacon scanner cannot exceed maximum allowable timeout.
        """
        if value is not None:
            if not isinstance(value, (float, int)):
                raise TypeError("Beacon scanner timeout must be a float, "
                        "integer, or NoneType.")
            elif value <= 0:
                raise ValueError("Beacon scanner timeout must be strictly "
                        "positive.")
            elif value > MAX_TIMEOUT:
                raise ValueError("Beacon scanner timeout cannot exceed "
                        "maximum allowable timeout.")
        self.__timeout = value
    
    @property
    def revisit(self):
        """BLE beacon scanner revisit interval getter."""
        return self.__revisit

    @revisit.setter
    def revisit(self, value):
        """BLE beacon scanner revisit interval setter.

        Raises:
            TypeError: Beacon scanner revisit interval must be an integer.
            ValueError: Beacon scanner revisit interval must be strictly 
                positive.
         """
        if not isinstance(value, int):
            raise TypeError("Beacon scanner revisit interval must be an "
                    "integer.")
        elif value <= 0:
            raise ValueError("Beacon scanner revisit interval must strictly "
                    "positive.")
        self.__revisit = value
    
    @property
    def filters(self):
        """BLE beacon scanner filters getter."""
        return self.__filters
    
    @filters.setter
    def filters(self, value):
        """BLE beacon scanner filters setter.

        Raises:
            TypeError: Beacon scanner filters must be a dictionary.
            KeyError: Beacon scanner filters must be one of allowable filters.
        """
        if not isinstance(value, dict):
            raise TypeError("Beacon scanner filters must be a dictionary.")
        elif not all([key in ALLOWABLE_FILTERS for key in value.keys()]):
            raise KeyError("Beacon scanner filters must be one of allowable "
                    f"filters {ALLOWABLE_FILTERS}.")
        self.__filters = value
    
    def filter_advertisements(self, advertisements):
        """Filter received beacon advertisements based on filters.
        
        Args:
            advertisements (pandas.DataFrame): Parsed advertisements.
            
        Returns:
            Advertisements with all entries that were not compliant with the 
            filters removed.
        """
        for key, value in self.filters.items():
            # Filter based on fixed identifiers
            if key in ID_FILTERS:
                advertisements = advertisements[advertisements[key].isin([value])]
            # Filter based on measurements
            else:
                query_str = f"{value[0]} <= {key} and {key} <= {value[1]}"
                advertisements = advertisements.query(query_str)
        advertisements.reset_index(inplace=True, drop=True)
        return advertisements
    
    def process_scans(self, scans, timestamps):
        """Process collection of received beacon advertisement scans.
        
        Organize collection of received beacon advertisement scans according 
        to address, payload, and measurements.

        Args:
            scans (list): Received beacon advertisement scans. Each element 
                contains all advertisements received from one scan. Elements 
                are in temporal order.
            timestamps (list): Timestamps associated with each scan.
            
        Returns:
            Advertisements organized in a pandas.DataFrame by address first, 
            timestamp second, and then remainder of advertisement payload, 
            e.g., UUID, major, minor, etc.
        """
        # Collect all advertisements
        advertisements = []
        for (scan, timestamp) in zip_longest(scans, timestamps):
            for address, payload in scan.items():
                advertisement = {'ADDRESS': address, 'TIMESTAMP': timestamp}
                advertisement['UUID'] = payload[0]
                advertisement['MAJOR'] = payload[1]
                advertisement['MINOR'] = payload[2]
                advertisement['TX POWER'] = payload[3]
                advertisement['RSSI'] = payload[4]
                advertisements.append(advertisement)
        # Format into DataFrame
        return  pd.DataFrame(advertisements,columns=['ADDRESS', 'TIMESTAMP', 
            'UUID', 'MAJOR', 'MINOR', 'TX POWER', 'RSSI'])

    def scan(self, scan_prefix='', timeout=0, revisit=1):
        """Execute BLE beacon scan.
        
        Args:
            scan_prefix (str): Scan output file prefix. Final output file name
                will be appended with first scan start timestamp. Defaults to
                configuration value.
            timeout (int, float): Time (s) for which to advertise beacon. If 
                specified as None then advertises till user commanded stop via 
                control file. Defaults to configuration value.
            revisit (int): Time interval (s) between consecutive scans. 
                Defaults to 1.
            
        Returns:
            Filtered advertisements organized in a pandas.DataFrame by address 
            first, timestamp second, and then remainder of advertisement 
            payload, e.g., UUID, major, minor, etc.
        """
        # Parse inputs
        if scan_prefix == '':
            scan_prefix = self.scan_prefix
        if timeout == 0:
            timeout = self.timeout
        # Update control file and scan output file
        with open(self.__control_file, 'w') as f:
            f.write("0")
        scan_file = Path(f"{scan_prefix}_{datetime.now():%Y%m%dT%H%M%S}.csv")
        # Start advertising
        self.__logger.info(f"Starting beacon scanner with timeout {timeout}.")
        self.__control_file_handle = self.__control_file.open(mode='r+')
        run = True        
        timestamps = []
        scans = []
        scan_count = 0
        start_time = time.monotonic()
        while run:
            scan_count += 1
            self.__logger.debug(f"Performing scan #{scan_count} at revisit "
                    f"{self.revisit}.")
            timestamps.append(datetime.now())
            scans.append(self.__service.scan(self.revisit))
            # Stop advertising based on either timeout or control file
            if timeout is not None:
                if (time.monotonic()-start_time) > timeout:
                    self.__logger.debug("Beacon scanner timed out.")
                    run = False
            self.__control_file_handle.seek(0)
            control_flag = self.__control_file_handle.read()
            if control_flag != "0":
                self.__logger.debug("Beacon scanner control flag set to stop.")
                run = False
        self.__logger.info("Stopping beacon scanner.")
        # Cleanup
        self.__control_file_handle.close()
        with self.__control_file.open('w') as f:
            f.write("0")
        # Process, filter, and output received scans
        advertisements = self.process_scans(scans, timestamps)
        advertisements = self.filter_advertisements(advertisements)
        advertisements.to_csv(scan_file, index_label='SCAN')
        return advertisements
    
def setup_logger(config):
    """Setup and return logger based on configuration."""
    logging.config.dictConfig(config['config'])
    return logging.getLogger(config['name'])
    
def close_logger(logger):
    """Close logger."""
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)
    
def load_config(parsed_args):
    """Load configuration.

    Loads beacon/scanner configuration from parsed input argument. Any
    expected keys not specified use values from default configuration.

    Args:
        parsed_args (Namespace): Parsed input arguments.
        
    Returns:
        Configuration dictionary.
    """
    # Load default configuration if none specified
    if parsed_args['config_yml'] is None:
        config = DEFAULT_CONFIG
    # Load configuration YAML
    else:
        with open(parsed_args['config_yml'], 'r') as f:
            config = yaml.load(f, Loader=yaml.SafeLoader)
        config['advertiser'] = {**DEFAULT_CONFIG['advertiser'], 
                **config['advertiser']}
        config['scanner'] = {**DEFAULT_CONFIG['scanner'], 
                **config['scanner']}
    # Merge configuration values with command line options
    for key, value in parsed_args.items():
        if value is not None:
            if key in config['advertiser']:
                config['advertiser'][key] = value
            if key in config['scanner']:
                config['scanner'][key] = value
    # Remove malformed filters
    if config['scanner']['filters'] is not None:
        filters_to_remove = []
        for key, value in config['scanner']['filters'].items():
            if key not in ALLOWABLE_FILTERS:
                filters_to_remove.append(key)
            elif value is None:
                filters_to_remove.append(key)
            elif key in MEASUREMENT_FILTERS and len(value) != 2:
                filters_to_remove.append(key)
        for filter_to_remove in filters_to_remove:
            del config['scanner']['filters'][filter_to_remove]
    return config
    
def parse_args(args):
    """Input argument parser.

    Args:
        args (list): Input arguments as taken from sys.argv.
        
    Returns:
        Dictionary containing parsed input arguments. Keys are argument names.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description=("BLE beacon advertiser or scanner. Command line "
                     "arguments will override their corresponding value in "
                     "a configuration file if specified."))
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('-a', '--advertiser', action='store_true',
                            help="Beacon advertiser mode.")
    mode_group.add_argument('-s', '--scanner', action='store_true',
                            help="Beacon scanner mode.")
    parser.add_argument('--config_yml', help="Configuration YAML.")
    parser.add_argument('--control_file', help="Control file.")
    parser.add_argument('--scan_prefix', help="Scan output file prefix.")
    parser.add_argument('--timeout', type=float, 
            help="Timeout (s) for both beacon advertiser and  scanner modes.")
    parser.add_argument('--uuid', help="Beacon advertiser UUID.")
    parser.add_argument('--major', type=int, 
            help="Beacon advertiser major value.")
    parser.add_argument('--minor', type=int, 
            help="Beacon advertiser minor value.")
    parser.add_argument('--tx_power', type=int, 
            help="Beacon advertiser TX power.")
    parser.add_argument('--interval', type=int,
            help="Beacon advertiser interval (ms).")
    parser.add_argument('--revisit', type=int, 
            help="Beacon scanner revisit interval (s)")
    return vars(parser.parse_args(args))
    
def main(args):
    """Creates beacon and either starts advertising or scanning.
    
    Args:
        args (list): Arguments as provided by sys.argv.

    Returns:
        If advertising then no output (None) is returned. If scanning 
        then scanned advertisements are returned in pandas.DataFrame.
    """
    # Initial setup
    parsed_args = parse_args(args)
    config = load_config(parsed_args)
    logger = setup_logger(config['logger'])
    logger.debug(f"Beacon configuration - {config['advertiser']}")
    logger.debug(f"Scanner configuration - {config['scanner']}")
    
    # Create and start beacon advertiser or scanner
    try:
        if parsed_args['advertiser']:
            logger.info("Beacon advertiser mode selected.")
            advertiser = Advertiser(logger, **config['advertiser'])
            advertiser.advertise()
            output = None
        elif parsed_args['scanner']:
            logger.info("Beacon scanner mode selected.")
            scanner = Scanner(logger, **config['scanner'])
            advertisements = scanner.scan()
            output = advertisements
    except Exception:
        logger.exception("Fatal exception encountered")
    finally:
        close_logger(logger)
    return output
    
if __name__ == "__main__":
    """Script execution."""
    main(sys.argv[1:])
    
