# role : check_ntp
This role determines the synchronized status of Network Time Protocol (NTP).
It is supported on a variety of platforms and helps embed error checking
into playbooks without manually performing ask-and-check operations.

## Hosts
This role can be applied to one of three types of hosts:
  * Physical Cisco ASA running in single context mode
  * Virtual Cisco ASAv
  * Physical Cisco IOS and IOS-XE devices (routers, switches, etc.)
  * Virtual Cisco IOS and IOS-XE devices (CSR1000v, etc.)

Each host included must device a host variable called `ansible_network_os`
which must be one of the following:
  * `ios`: For any IOS or IOS-XE device
  * `asa_single`: For any single context ASA
  * `asa_multi`: For any single context ASA

## Variables
The role defines a single default variable called `synchronized`. True by
default, this value determines whether NTP should be synchronized or not.
Sometimes, overriding this default to false allows a playbook designer to
ensure NTP is not synchronized to avoid false positives, such as when testing
a new system that is known to not be synchronized.

## Role tasks (summarized)
The action of communicating with a network device to pull NTP status is
abstracted into a separate tasks file. The naming of the files will exactly
match the `ansible_network_os` defined earlier, except prepended with `tasks_`
and appended with `.yml`. This is dynamically included at runtime based on the
type of device being verified.
