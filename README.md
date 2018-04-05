# power_module
This repository is intended for use with current_sensing power module.

Documentations for selecting the hardware and instruments can be found in "doc"
Basic test scripts can be found in "i2c-test"

For running measurements:
- measure.py is the code to run on the drone, to measure motors currents, as well as receiving information from the agent, and recording them in log files.
- constant.py is a configuration file imported in measure.py
- tcp_client.py is a test code to run and act as the agent to send some commands to the measure.py manually.

All graph related scripts are in "graph", the ones in 2016 are not necessarily kept anymore, be careful.



---------------------------------------------------
measurement procedure:
* Note that the time of the system is correct before logging. if not, set it manually.
sudo date -s "2017-05-25 00:00"

