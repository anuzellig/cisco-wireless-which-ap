# Which AP?
A simple web application for use with Cisco 9800 Series or Embedded Wireless controllers which uses NETCONF to provide some useful info about the client. It can be useful for troubleshooting wireless connectivity issues, quickly discovering which access point a client is connected to from the client, troubleshooting roaming, etc. 

![Sample screenshot](https://github.com/anuzellig/cisco-wireless-which-ap/blob/main/screenshots/IMG_6442.jpeg?raw=true)


## Usage
The configuration parameters are read from environment variables by the script. On Linux/macOS you can launch the script from the shell like this:

	HOST=<Wireless Controller hostname or IP> USERNAME=<admin username> PASSWORD=<admin password> python which-ap.py
	
Or on Windows:

	cmd /C "HOST =<Wireless Controller hostname or IP> && set USERNAME=<admin username> && set PASSWORD=<admin password> python monitor-which-ap.py"

And then from your wireless client browse to the IP address of the host that is running the script on port 5001, i.e. `http://<ip>:5001`


## Notes

* The script relies on retrieving the IP address of the client. If you are running this from a container and your container hosting solution normally performs SNAT you'll want to configure it such that it preserves the source address for this container, e.g. using `host` networking mode. 
* It has only been tested with the Cisco Embedded Wireless Controller, but should also work with the 9800 Series. 


This project is not affiliated with or supported by Cisco Systems. 