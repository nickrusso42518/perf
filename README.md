# Performance Testers
This series of playbooks accomplish a number of performance test
tasks in the network. They are briefly described below, either each
one becoming more time consuming and comprehensive than the one before it.

  * `sperf`: Short-term performance test builds a matrix of average
    RTT times. This is suitable for general public distribution. Unlike
    other tests, the number of columns is dynamic based on the target
    list.

  * `mperf`: Mid-term performance test builds a matrix of data from
    many subcomponents, listed below. It is provided to engineers only.
    * IP SLA udp-jitter to capture detailed performance metrics
    * ICMP ping to probe for MTU/fragmentation problems
    * MPLS ping (LSPV) to test MPLS label switch path health

  * `lperf`: Long-term performance test focuses on detailed performance
    data collected over hours. It is provided in support of sustained
    efforts or as proof to your SP that they are not meeting their SLAs.

Given these reachability results, some basic conclusions about the
state of the network are drawn and summarized in a synopsis for each target.
Collected information is rolled up in a master CSV file for quick reference.
Again, the length and composition of each CSV file differs between the 3 tests.

> Contact information:
> Email:    njrusmc@gmail.com
> Twitter:  @nickrusso42518

  * [Supported platforms](#supported-platforms)
  * [Hosts](#hosts)
  * [Variables](#variables)
  * [Templates](#templates)
  * [LSPV Codes](#lspv-codes)
  * [IP SLA Columns](#ip-sla-columns)

## Supported platforms
Cisco IOS routers are supported today. The routers need to be on a version
that supports the exec command set `ip sla udp-jitter` and `ping mpls ipv4`
in order to function with the `mperf` and `lperf` playbooks. All three
playbooks require basic ICMP `ping` functionality, which all Cisco IOS
routers support.

Testing was conducted on the following platforms and versions:
  * Cisco CSR1000v, version 16.07.01a, running in AWS

## Hosts
All Cisco IOS MPLS routers in the `perf_routers` group are in scope. Normally,
the playbook runs what is effectively a full IP/MPLS reachability test in the
global table. For a more rapid test, you can modify the `targets` list to
include only some routers, while also changing the hosts in scope. These
combination approaches are also supported. For example, maybe logging into
one router per region then targeting 2 routers in every other region
provides a sufficient picture of the current network performance.

The following are __REQUIRED__ for this playbooks to work:
  * All routers must be in a group containing the string `"region"`
  * All routers must be in exactly one of these regional groups
  * All regional groups must be children of `perf_routers`
  * Each regional group must have a corresponding `regional_sla` dict.
    This provides the SLA committments to all other regions, including
    its own (intra-regional SLA).

```
# hosts.yml
---
all:
  hosts:
    localhost:
  children:
    perf_routers:
      children:
        usa_region:  # AWS North Virginia, USA
          hosts:
            csr1:
            csr2:
        emear_region:  # AWS Frankfurt, Germany
          hosts:
            csr3:
...
```

Below are two examples of group variables files, one per region.

```
# group_vars/usa_region.yml
---
regional_sla:
  usa_region: 30
  emear_region: 88  # Aggressive SLA chosen to show over threshold counters
...
```

```
# group_vars/emear_region.yml
---
regional_sla:
  usa_region: 120  # Conservative SLA chosen to show good performance
  emear_region: 40
...`
```

## Variables
These playbooks rely only on `group_vars` which are defined for the general
router group. The main variable is a sequence called `targets` which lists the
__global__ hostname of any remote host. Nodes not yet activated/configured
should still be added to the list; the playbook has the intelligence to
only consider "online" targets based on /32 FIB entries present.
To save processing time, this collection of "online" targets is only run
on one host then referenced from the rest. The output parsing
is accomplished using the `intersect_block` custom filter.

Regional SLA values were discussed above as they are more relevant to
hosts (and their geographic locations) than they are to general playbook
operation.

As a minor `mperf` option, operators can modify the IP SLA repeat count.
For quick reachability testing, the repeat count should be small. For
reliable performance testing, the repeat count should be high. __Note that
probes that run too long or incur too much loss will simply fail to provide
any results, which is a shortcoming of the IP SLA feature when invoked
from the exec shell.__

The `state` variable is only relevant for long-term probes since the
`lperf_put` playbook will add or remove them, depending. The time
is the amount of time the probe should run and must be between 1-24.
The state can be `present`, `absent`, or `restarted` only.
Only the most recent complete hour of statistics is available
when long-term performance metrics are retrieved. This is a limitation
of the current playbook implementation, and may be improved in a
future revision. The repeat count is only valid for the
`mperf` playbook.

One final note: The targets in this list __must__ be loopback0 IP addresses.
This limitation may seem arbitrary, but it simplifies the code and generally
makes sense, since we are testing reachability of MPLS LSPs in many cases.
These IPs may not be the same IPs as those used for management of a given node
as specified in the inventory. For networks where devices are managed in-band
by their loopback0 IP addresses, the target name and the inventory name can
be the same.

```
---
DEVICE_TYPE: ios
state: present
time_hrs: 1
repeat: 10
targets:
  - id: 100101
    target: csr1_lb0
  - id: 100102
    target: csr2_lb0
...
```

## Templates
The templates are __NOT__ commented for readability in this playbook since
they are not used for issuing commands to a network device. Rather, the
template is used for transforming IOS output into a human-readable CSV file
for further analysis and archival. Many custom filters are used and are
individually documented in the Python source code, which can be
found in the `plugins/filter/filter.py` file.

__The templates should not be changed at the operator level.__

## LSPV Codes
The table below provides the LSPV codes which may appear in the `mperf`
sheets when testing MPLS reachability.

```
+------+-----------------------------------------------------------------------+
| CODE | MEANING                                                               |
+------+-----------------------------------------------------------------------+
| !    | success                                                               |
| Q    | request not sent                                                      |
| .    | timeout                                                               |
| L    | labeled output interface                                              |
| B    | unlabeled output interface                                            |
| D    | DS Map mismatch                                                       |
| F    | no FEC mapping                                                        |
| f    | FEC mismatch                                                          |
| M    | malformed request                                                     |
| m    | unsupported tlvs                                                      |
| N    | no label entry                                                        |
| P    | no rx intf label prot                                                 |
| p    | premature termination of LSP                                          |
| R    | transit router                                                        |
| I    | unknown upstream index                                                |
| l    | Label switched with FEC change                                        |
| d    | see DDMAP for return code                                             |
| X    | unknown return code                                                   |
| x    | return code 0                                                         |
+------+-----------------------------------------------------------------------+
```

## IP SLA Columns
The table below provides the detailed explanations for the abbreviated
column headers in the spreadsheet. This is used only for `mperf` and `lperf`
playbooks as `sperf` only shows average RTT for brevity.

```
+---------------+-------------------------------------------------------------+
| COLUMN NAME   | DETAILED EXPLANATION                                        |
+---------------+-------------------------------------------------------------+
| rtt_cnt       | Number Of RTT received                                      |
| rtt_min       | RTT Minimum (ms)                                            |
| rtt_avg       | RTT Average (ms)                                            |
| rtt_max       | RTT Maximum (ms)                                            |
| rtt_ovthr     | Number Of RTT Over Threshold                                |
| rtt_ovthp     | Percentage Of RTT Over Threshold                            |
| lat_cnt       | Number of Latency one-way Samples                           |
| lat_sd_min    | Source to Destination Latency one way Minimum (ms)          |
| lat_sd_avg    | Source to Destination Latency one way Average (ms)          |
| lat_sd_max    | Source to Destination Latency one way Maximum (ms)          |
| lat_ds_min    | Destination to Source Latency one way Minimum (ms)          |
| lat_ds_avg    | Destination to Source Latency one way Average (ms)          |
| lat_ds_max    | Destination to Source Latency one way Maximum (ms)          |
| jit_sd_cnt    | Number of Source to Destination Jitter Samples              |
| jit_sd_min    | Source to Destination Jitter Minimum (ms)                   |
| jit_sd_avg    | Source to Destination Jitter Average (ms)                   |
| jit_sd_max    | Source to Destination Jitter Maximum (ms)                   |
| jit_ds_cnt    | Number of Destination to Source Jitter Samples              |
| jit_ds_min    | Destination to Source Jitter Minimum (ms)                   |
| jit_ds_avg    | Destination to Source Jitter Average (ms)                   |
| jit_ds_max    | Destination to Source Jitter Maximum (ms)                   |
| los_sd        | Loss Source to Destination                                  |
| los_sd_per    | Source to Destination Loss Periods Number                   |
| los_sd_pmin   | Source to Destination Loss Period Length Minimum (ms)       |
| los_sd_pmax   | Source to Destination Loss Period Length Maximum (ms)       |
| los_sd_imin   | Source to Destination Inter Loss Period Length Minimum (ms) |
| los_sd_imax   | Source to Destination Inter Loss Period Length Maximum (ms) |
| los_ds        | Loss Destination to Source                                  |
| los_ds_per    | Destination to Source Loss Periods Number                   |
| los_ds_pmin   | Destination to Source Loss Period Length Minimum (ms)       |
| los_ds_pmax   | Destination to Source Loss Period Length Maximum (ms)       |
| los_ds_imin   | Destination to Source Inter Loss Period Length Minimum (ms) |
| los_ds_imax   | Destination to Source Inter Loss Period Length Maximum (ms) |
| pkt_ooseq     | Packets Out Of Sequence                                     |
| pkt_tdrop     | Packets Tail Dropped                                        |
| pkt_late      | Packets Arrived Late                                        |
| pkt_skip      | Packets Skipped                                             |
| voc_mos_min   | Mean Opinion Score (MOS) Minimum: 0.00-5.00                 |
| voc_mos_max   | Mean Opinion Score (MOS) Maximum: 0.00-5.00                 |
| voc_icpif_min | Calculated Planning Impairment Factor (ICPIF) Minimum: 1-20 |
| voc_icpif_max | Calculated Planning Impairment Factor (ICPIF) Maximum: 1-20 |
+---------------+-------------------------------------------------------------+
```
