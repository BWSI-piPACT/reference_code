# BWSI piPACT Reference Code
BWSI piPACT Reference/instructor developed code for Raspberry Pi based BLE RSSI measurement collection.

# Requirements
Stated versions are tested and validated. Newer or older versions are not guaranteed to work.

- Python 3.7.3
- pybluez[ble]
- gattlib
- numpy
- pandas
- pyyaml

# Installation
1. Install the requirement.
2. Clone the repository.
3. Navigate into the `reference_code` folder that was created.
   ```console
   pi@raspberrypi:~ $ cd reference_code
   ```
4. Test the repository by attempting to import the piPACT reference code without error.
   ```console
   pi@raspberrypi:~/reference_code $ python3
   Python 3.7.3 (default, Dec 20 2019, 18:57:59) 
   [GCC 8.3.0] on linux
   Type "help", "copyright", "credits" or "license" for more information.
   >>> import pi_pact
   >>>
   ```
   
# Usage
This section addresses how to use the reference code to instantiate either a beacon advertiser or beacon scanner from the command line/terminal. Both are accessed from the same command line interface and use a common configuration file. Both also implement "user commanded stop" functionality via a simple control file mechanism explained in each section.

```console
pi@raspberrypi:~ $ sudo python3 pi_pact.py --help
usage: pi_pact.py [-h] (-a | -s) [--config_yml CONFIG_YML]
                  [--control_file CONTROL_FILE] [--scan_prefix SCAN_PREFIX]
                  [--timeout TIMEOUT] [--uuid UUID] [--major MAJOR]
                  [--minor MINOR] [--tx_power TX_POWER] [--interval INTERVAL]
                  [--revist REVIST]

BLE beacon advertiser or scanner. Command line arguments will override their
corresponding value in a configuration file if specified.

optional arguments:
  -h, --help            show this help message and exit
  -a, --advertiser      Beacon advertiser mode.
  -s, --scanner         Beacon scanner mode.
  --config_yml CONFIG_YML
                        Configuration YAML.
  --control_file CONTROL_FILE
                        Control file.
  --scan_prefix SCAN_PREFIX
                        Scan output file prefix.
  --timeout TIMEOUT     Timeout (s) for both beacon advertiser and scanner
                        modes.
  --uuid UUID           Beacon advertiser UUID.
  --major MAJOR         Beacon advertiser major value.
  --minor MINOR         Beacon advertiser minor value.
  --tx_power TX_POWER   Beacon advertiser TX power.
  --interval INTERVAL   Beacon advertiser interval (ms).
  --revist REVIST       Beacon scanner revisit interval (s)
```

## Configuration
The configuration file is of the YAML format. It is provided with a default configuration which you should change to suit your needs. You will need to reference in-line comments and external module documentation to fully understand all configuration options. 

The configuration YAML will only be used if specified as a commadn line argument. Many indiviudal configuration options can be overwritten by command line provided arguments.

```yaml
# Configuration file for piPACT reference collection software

# Settings for iBeacon advertisment
advertiser:
  control_file: 'advertiser_control' # Control file which stops beacon advertisement before timeout
  timeout: 20 # Advertisement timeout (s)
  uuid: '' # UUID, major, and minor values to advertise
  major: 1
  minor: 1 
  tx_power: 1 # Tx power at which to advertise
  interval: 200 # Interval at which advertise (ms)

# Settings for beacon scanner
scanner:
  control_file: 'scanner_control' # Control file which stops beacon scanner before timeout
  scan_prefix: 'pi_pact_scan' # Prefix to attach to scan output files
  timeout: 20 # Scanning timeout (s)
  revisit: 1 # Interval at which to scan (s)
  filters: # Filters
    ADDRESS:
    RSSI:
    
# Logger configuration
logger:
  name: &name 'pi_pact.log'
  config:
    version: 1
    formatters:
      full:
        format: '%(asctime)s   %(module)-10s   %(levelname)-8s   %(message)s'
      brief:
        format: '%(asctime)s   %(levelname)-8s   %(message)s'
    handlers:
      console:
        class: 'logging.StreamHandler'
        level: 'INFO'
        formatter: 'brief'
      file:
        class: 'logging.handlers.TimedRotatingFileHandler'
        level: 'DEBUG'
        formatter: 'full'
        filename: *name
        when: 'H'
        interval: 1
    loggers:
      *name:
        level: 'DEBUG' # Effective logging level
        handlers:
          - 'console'
          - 'file'
```

## Advertiser
An advertiser can be started in one of two primary modes concerning when and how to stop the advertiser. In either case, the user commanded stop is available.

### No Timeout
In this mode, the advertiser will run infinitely until a user commanded stop is specified via the advertiser control file. The advertiser control file is specified either in the configuration YAML or overwritten by the command line argument.

1. Start the advertiser. The addition of the `&` flag causes the command to be executed in the background. This allows the user to retain control of the command line which makes commanding the advertiser to stop much easier.
   ```console
   pi@raspberrypi:~ $ sudo python3 pi_pact.py -a --config_yml pi_pact_config.yml &
   [1] 2083
   ``` 
2. Observe the informational log messages.
   ```console
   pi@raspberrypi:~ $ 2020-06-20 10:12:42,594   INFO       Beacon advertiser mode selected.
   2020-06-20 10:12:42,597   INFO       Initialized beacon advertiser.
   2020-06-20 10:12:42,599   INFO       Starting beacon advertiser with timeout None.
   ```
3. Stop the advertiser by placing any non-zero value into the advertiser control file.
   ```console
   pi@raspberrypi:~ $ echo 1 > advertiser_control
   pi@raspberrypi:~ $ 2020-06-20 10:12:58,623   INFO       Stopping beacon advertiser.
   ```

### Timeout
In this mode, the advertiser will run either until the specified timeout or until a user commanded stop is specified via the advertiser control file. The advertiser control file is specified either in the configuration YAML or overwritten by the command line argument.

1. Start the advertiser. The addition of the `&` flag causes the command to be executed in the background. This allows the user to retain control of the command line which makes commanding the advertiser to stop much easier.
   ```console
   pi@raspberrypi:~ $ sudo python3 pi_pact.py -a --config_yml pi_pact_config.yml --timeout 20 &
   [1] 2282
   ``` 
2. Observe the informational log messages.
   ```console
   pi@raspberrypi:~ $ 2020-06-20 10:26:10,268   INFO       Beacon advertiser mode selected.
   2020-06-20 10:26:10,270   INFO       Initialized beacon advertiser.
   2020-06-20 10:26:10,273   INFO       Starting beacon advertiser with timeout 20.0.
   ```
3. Stop the advertiser either by waiting for the timeout
   ```console
   2020-06-20 10:26:30,301   INFO       Stopping beacon advertiser.
   ```
   or by placing any non-zero value into the advertiser control file.
   ```console
   pi@raspberrypi:~ $ echo 1 > advertiser_control
   pi@raspberrypi:~ $ 2020-06-20 10:26:30,301   INFO       Stopping beacon advertiser.
   ```

## Scanner
A scanner can be started in one of two primary modes concerning when and how to stop the scanner. In either case, the user commanded stop is available.

### No Timeout
In this mode, the scanner will run infinitely until a user commanded stop is specified via the scanner control file. The scanner control file is specified either in the configuration YAML or overwritten by the command line argument.

1. Start the scanner. The addition of the `&` flag causes the command to be executed in the background. This allows the user to retain control of the command line which makes commanding the scanner to stop much easier.
   ```console
   pi@raspberrypi:~ $ sudo python3 pi_pact.py -s --config pi_pact_config.yml &
   [1] 2083
   ``` 
2. Observe the informational log messages.
   ```console
   pi@raspberrypi:~ $ 2020-06-20 10:12:42,594   INFO       Beacon scanner mode selected.
   2020-06-20 10:12:42,597   INFO       Initialized beacon scanner.
   2020-06-20 10:12:42,599   INFO       Starting beacon scanner with timeout None.
   ```
3. Stop the scanner by placing any non-zero value into the scanner control file.
   ```console
   pi@raspberrypi:~ $ echo 1 > scanner_control
   pi@raspberrypi:~ $ 2020-06-20 10:12:58,623   INFO       Stopping beacon scanner.
   ```

### Timeout
In this mode, the scanner will run either until the specified timeout or until a user commanded stop is specified via the scanner control file. The scanner control file is specified either in the configuration YAML or overwritten by the command line argument.

1. Start the scanner. The addition of the `&` flag causes the command to be executed in the background. This allows the user to retain control of the command line which makes commanding the scanner to stop much easier.
   ```console
   pi@raspberrypi:~ $ sudo python3 pi_pact.py -s --config pi_pact_config.yml --timeout 20 &
   [1] 2282
   ``` 
2. Observe the informational log messages.
   ```console
   pi@raspberrypi:~ $ 2020-06-20 10:26:10,268   INFO       Beacon scanner mode selected.
   2020-06-20 10:26:10,270   INFO       Initialized scanner advertiser.
   2020-06-20 10:26:10,273   INFO       Starting beacon scanner with timeout 20.0.
   ```
3. Stop the advertiser either by waiting for the timeout
   ```console
   2020-06-20 10:26:30,301   INFO       Stopping beacon scanner.
   ```
   or by placing any non-zero value into the scanner control file.
   ```console
   pi@raspberrypi:~ $ echo 1 > scanner_control
   pi@raspberrypi:~ $ 2020-06-20 10:26:30,301   INFO       Stopping beacon scanner.
   ```
   
# Output
The only explicit output of this code are the published log messages (console and log file) and CSV files containing the beacons found by the beacon scanner. The default (and expected) format/headers of this CSV file are as follow.
- SCAN: The scan number during which this beacon advertisement was received.
- ADDRESS: The address of the beacon.
- TIMESTAMP: Timestamp (in beacon scanner device's time) at which this beacon advertisement was received.
- UUID: The UUID sent in beacon advertisement.
- MAJOR: The major value sent in beacon advertisement.
- MINOR: The minor value sent in beacon advertisement.
- TX POWER: The Tx power value sent in beacon advertisement.
- RSSI: The measured RSSI (dBm) of the received beacon advertisement.
