# piPACT Raspberry Pi Setup
This document explains how to setup a Raspberry Pi, specifically its OS and system settings, for piPACT. The overall OS and system settings that are implemented by these instructions are captured in the [preconfigured OS image](https://drive.google.com/file/d/1HNnyF63N6r_fmepIvHKHla1A_UYT0AoL/view?usp=sharing). There are steps that will need to be done in any case and are highlighted appropriately. You will need to repeat this for each Raspberry Pi being set up.

For those interested in headless (without a monitor) Raspberry Pi setup, the information found [here](https://www.raspberrypi.org/documentation/configuration/wireless/headless.md) may be useful.

## Preconfigured Setup
This section addresses how to use the [preconfigured OS image](https://drive.google.com/file/d/1HNnyF63N6r_fmepIvHKHla1A_UYT0AoL/view?usp=sharing) to setup your Raspberry Pi.

### Requirements
- A computer with
  - microSD card comptability
  - Imaging software (e.g., [Balena Etcher](https://www.balena.io/etcher/))
- microSD card
- Monitor
- Keyboard
- Mouse

### Deploying Preconfigured OS Image
1. Download the [preconfigured OS image](https://drive.google.com/file/d/1HNnyF63N6r_fmepIvHKHla1A_UYT0AoL/view?usp=sharing) onto your computer.
2. Flash the image onto the microSD card using your imaging software. It's suggested you "validate" your image if your software provides such an option.

### Booting up Raspberry Pi
1. Connect your monitor, keyboard, and mouse to the Raspberry Pi.
2. Insert the microSD card into the Raspberry Pi.
3. Apply power to the Raspberry Pi.

### Changing Username/Password
1. Follow these [instructions](https://www.maketecheasier.com/change-raspberry-pi-password/) to create a new username and password.
2. It is recommended you disable the default `pi` account in order to secure your Raspberry Pi.

### Connect to WiFi
1. Follow these [instructions](https://www.raspberrypi.org/documentation/configuration/wireless/desktop.md) to connect your Raspberry Pi to your wireless network of choice. Be sure it is one you trust.

### Get piPACT Reference Code
1. [Clone](https://www.git-scm.com/docs/git-clone) the [piPACT reference code](https://github.com/BWSI-piPACT/reference_code).
2. Test the code by attempting to import it in Python.
   ```console
   pi@raspberrypi:~ $ python3
   Python 3.7.3 (default, Dec 20 2019, 18:57:59) 
   [GCC 8.3.0] on linux
   Type "help", "copyright", "credits" or "license" for more information.
   >>> import pi_pact
   >>> exit()
   pi@raspberrypi:~ $ 
   ```

### Update Wireless Settings
1. Follow these [instructions](https://pimylifeup.com/raspberry-pi-static-ip-address/) to assign a static IP to your Raspberry Pi. We have prepopulated the `dhcpcd.conf` file with a commented out template of the static IP wireless configuration. You can either update this template and uncomment it or write your own according to the linked to instructions.
   
   Be sure to assign **unique** `<STATIC_IP>` amongst all the devices on your wireless network including other Raspberry Pis that you set up with static IPs.
   ```
   # piPACT wireless static IP configuration template
   interface wlan0
   static ip_address=<STATIC_IP>/24
   static routers=<ROUTER_IP>
   static domain_name_server=<DNS_IP>
   ```
2. If you didn't do so in the previous step, reboot your Pi for the wireless setting to take effect.

### Testing Wireless Access
1. From a computer with SSH capability and using the static IP you assigned previously, perform step 4 of these [instructions](https://www.raspberrypi.org/documentation/remote-access/ssh/).
2. If you have properly configured your Raspberry Pi for SSH via a static IP then you should be able to execute commands on the Raspberry Pi remotely.

## From "Scratch" Setup
These instructions are for those wanting to configure and deploy their Raspberry Pi from scratch, i.e., without using the preconfigured OS image. Please note that these instructions are provided only for informational purposes.

### "Vanilla" Raspberry Pi OS
1. [Download](https://www.raspberrypi.org/downloads/raspberry-pi-os/) the image of your preferred version of Raspberry Pi OS. We recommend at least a "Desktop" version if not the one that includes "Recommended Sofware".
2. Flash the image onto the microSD card using your imaging software. It's suggested you "validate" your image if your software provides such an option.

### Booting up Raspberry Pi
1. Connect your monitor, keyboard, and mouse to the Raspberry Pi.
2. Insert the microSD card into the Raspberry Pi.
3. Apply power to the Raspberry Pi.
4. Follow the on-screen prompts to update system settings (clock, locale, keyboard, etc.), change username/password, select/configure the wireless network to connect to, and update packages.

### Configure Python
1. From the terminal, install required Debian packages by executing the following command:
   ```
   sudo apt-get install pkg-config libboost-python-dev libboost-thread-dev libbluetooth-dev libatlas-base-dev libglib2.0-dev python-dev
   ```
2. From the terminal, install required Python packages by executing the following command:
   ```
   sudo pip3 install gattlib pybluez[ble] numpy pandas pyyaml
   ```
   
### Get piPACT Reference Code
1. [Clone](https://www.git-scm.com/docs/git-clone) the [piPACT reference code](https://github.com/BWSI-piPACT/reference_code).
2. Test the code by attempting to import it in Python.
   ```console
   pi@raspberrypi:~ $ python3
   Python 3.7.3 (default, Dec 20 2019, 18:57:59) 
   [GCC 8.3.0] on linux
   Type "help", "copyright", "credits" or "license" for more information.
   >>> import pi_pact
   >>> exit()
   pi@raspberrypi:~ $ 
   ```
   
### Static IP Setup
1. Follow these [instructions](https://pimylifeup.com/raspberry-pi-static-ip-address/) to assign a static IP to your Raspberry Pi. Shown below is the structure of the additions/modifications to the `dhcpcd.conf` file.
   
   Be sure to assign **unique** `<STATIC_IP>` amongst all the devices on your wireless network including other Raspberry Pis that you set up with static IPs.
   ```
   # piPACT wireless static IP configuration template
   interface wlan0
   static ip_address=<STATIC_IP>/24
   static routers=<ROUTER_IP>
   static domain_name_server=<DNS_IP>
   ```
2. If you didn't do so in the previous step, reboot your Pi for the wireless setting to take effect.

### Testing Wireless Access
1. From a computer with SSH capability and using the static IP you assigned previously, perform step 4 of these [instructions](https://www.raspberrypi.org/documentation/remote-access/ssh/).
2. If you have properly configured your Raspberry Pi for SSH via a static IP then you should be able to execute commands on the Raspberry Pi remotely.
