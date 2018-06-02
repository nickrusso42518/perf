# Sample performance outputs
This folder contains a sample output comma-separated values (CSV) sheet
for each of the playbooks in this series. Normally, these would not be
version controlled, but are included to illustrate the value of the tools.

The sheets can be opened with Microsoft Excel and other spreadsheet tools.
They can also be viewed (with panning) from the shell using this command:

`column -s, -t <path/to/sheet.csv> | less -S`

## Short-term performance test (sperf)

The `sperf` sheet shows a matrix with the inventory hosts along the leftmost
column and the target hostnames along the top row. In a full-mesh style of
test (as shown here), the matrix will be a square and the diagonal will be
blanked out since there is no value in a node pinging itself. When the
list of targets is greater than the list of inventory hosts (for example,
the playbook logs into 5 hosts but tests reachability to 10), the table will
be 5 rows deep and 10 columns wide. The opposite is true when the number of
inventory hosts is greater than the number of targets; this combination is
rare.

Unlike `mperf` and `lperf`, the output is compact enough to also embed
directly into this README. This output has been formatted using the `column`
command showed above for easier viewing.

```
$ column -s, -t sperf_20180602T153856.csv
      csr1_lb0  csr2_lb0  csr3_lb0
csr1            1         88
csr2  1                   88
csr3  89        88
```

## Mid-term performance test (mperf)

The `mperf` sheet has a fixed column width and variable number of rows. Each
row represents a set of probe tests between endpoints. Each column details a
specific metric as detailed in the main README file. Because GRE tunnels were
used in AWS for the testing in this documentation, the performance tester
identified a potential MTU issue since a full 1500 byte packet cannot be sent
without fragmentation.

## Long-term performance test (lperf)

The `lperf` sheet is similar to `mperf` except adds additional performance
data while removing MPLS LSP health and MTU data. Notice the over-threshold
counter being large for the USA-to-EMEAR column as a result of the overly
strict SLA used for the test. The EMEAR-to-USA flows have fewer over threshold
hits because hte SLA in that direction was defined as more conservative.
__These numbers are for testing only.__ Being able to check over-threshold hits
can be very useful when raising concerns to a service provider. Recall that
the `lperf_put` playbook adds/removes probes from the configuration and
the `lperf_get` playbook collects statistics and creates the output CSV file.
