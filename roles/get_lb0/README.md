This role captures the Loopback0 IP address and subnet mask from
a Cisco IOS device. It is primarily used to determine the source IP
when using synthetic traffic (ping, MPLS LSPV, IP SLA, etc.) to
test network reachability. It can also be used to populate fields
on a spreadsheet relating to source/node IP addresses.

## Hosts
Typically this role is included in a play that contains several Cisco
IOS hosts, such as routers and switches.

## Role tasks (summarized)
This simple role logs into a Cisco IOS device, looks for the IP
information on Loopback0, and stores it in a variable called `LB0`.
This is a dictionary (hash) returned by the custom Python filter
called `ios_parse_ip`. The structure is as follows:

```
---
LB0:
  full_str: "10.0.0.1/32"
  address: "10.0.0.1"
  subnet: 32
...
```

The subnet field is an integer value while the other two are strings.
The `full_str` is typically only useful for pretty-printing. The role
automatically performs basic error checking after collecting this
information to ensure the `subnet` is exactly 32 and that the `address`
is a valid IPv4 address.
