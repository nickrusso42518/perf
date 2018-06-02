#!/usr/bin/python
'''
Author: Nick Russo <njrusmc@gmail.com>

File contains custom filters for use in Ansible playbooks.
https://www.ansible.com/
'''

from __future__ import print_function
import re
import socket
class FilterModule(object):
    '''
    Defines a filter module object.
    '''

    @staticmethod
    def filters():
        '''
        Return a list of hashes where the key is the filter
        name exposed to playbooks and the value is the function.
        '''
        return {
            'resolve': FilterModule.resolve,
            'ios_ipsla_stats': FilterModule.ios_ipsla_stats,
            'ios_ipsla_csv': FilterModule.ios_ipsla_csv,
            'ios_ping_stats': FilterModule.ios_ping_stats,
            'ios_ping_csv': FilterModule.ios_ping_csv,
            'intersect_block': FilterModule.intersect_block,
            'ios_parse_ip': FilterModule.ios_parse_ip,
            'perf_synopsis': FilterModule.perf_synopsis,
            'get_sla': FilterModule.get_sla
        }

    @staticmethod
    def intersect_block(text, cp_hash_list):
        '''
        This filter takes a block of text and a list of Cisco
        ping hashes. Each ipv4addr within the hash list is checked
        for presence within the block of text. This is useful for
        checking the presence of a route within a RIB/FIB, ultimately
        showing which targets to ping and which ones to skip. The
        list returned is a subset of the hash list parameter of
        only the hashes containing an ipv4addr which was present
        within the text block. The filter returns false only if
        there is a logic error whereby the subset is greater than
        the original parameter in length, which should be impossible.
        '''
        intersect_list = []
        for d in cp_hash_list:
            if d['ipv4addr'] in text:
                intersect_list.append(d)
        # Sanity check; new list cannot be longer than original
        if len(intersect_list) > len(cp_hash_list):
            return False
        return intersect_list


    @staticmethod
    def _try_int(val, base=10):
        '''
        Trivial integer parser that tries to extract an integer
        (base 10 by default) from a string. If it fails, the function
        returns the original input unmodified, as would be the case
        if the input were a string or float, for example.
        '''
        try:
            return int(val, base)
        except ValueError:
            # Just return the input as is
            return val

    @staticmethod
    def resolve(key):
        '''
        Given an IPv4 or hostname as input (key), the other value can
        be discovered. When the key is a string, the return type is
        a single hash with the original key, ipv4 addr, and hostname
        as key names (and corresponding values). The hostname only contains
        the first hostname, not a list of all hostnames. When the key
        is a list, a list of hahes in the same format described above
        are returned. When the key is any other type, the return value
        is False. If any errors are raised when resolving a given
        key, False is populated into the hostname and ipv4addr fields.
        Only the 'hosts' database can be used; this simplifies security.
        '''
        # print("resolve key is {0}".format(key))

        if isinstance(key, list):
            return FilterModule._resolve_list(key)
        elif isinstance(key, basestring):
            return FilterModule._resolve_host(key)

        # Some invalid value
        # print("input was not list or string, saw {0}".format(type(key)))
        return False

    @staticmethod
    def _resolve_host(key):
        '''
        Resolves a single host given a key and database.
        '''

        try:
            # Resolve the IPv4 address and hostname from the key
            new_ipv4 = socket.gethostbyname(key)
            # print("new_ipv4: {0}".format(new_ipv4))
            new_host = socket.gethostbyaddr(new_ipv4)[0]
            # print("new_host: {0}".format(new_host))
            d = {"key": key, "hostname": new_host, "ipv4addr": new_ipv4}
        except (socket.gaierror, socket.herror, TypeError):
            # need to add 'as ex' when uncommenting line below
            #print("Error for key '{0}': rc={1}".format(key, ex.returncode))
            d = {"key": key, "hostname": False, "ipv4addr": False}
        return d

    @staticmethod
    def _resolve_list(key_list):
        '''
        Resolves a list of hosts given a list of keys and a database.
        '''
        d_list = []
        for key in key_list:
            d = FilterModule._resolve_host(key)
            d_list.append(d)
        return d_list

    @staticmethod
    def ios_ipsla_stats(text):
        '''
        This filter parses through the relevant information from an
        exec-issued "ip sla udp-jitter" probe. This is useful for quickly
        collecting detailed statistics about the network performance. The
        return value is a hash that contains several self-explanatory keys
        containing values of the parsed information. The values are all
        strings at present though parsing them into ints/floats is
        an easy future enhancement.
        '''
        # Regex patterns for ints, double-ints, triple-ints, and floats are constant
        re_int = r'\d+'
        re_int2 = r'(\d+)/(\d+)'
        re_int3 = r'(\d+)/(\d+)/(\d+)'
        re_float = r'\d+\.\d+'

        # List of lookahead regexs to extract numbers
        re_list = [
            r'(?<=Number Of RTT: )' + re_int,
            r'(?<=RTT Min/Avg/Max: )' + re_int3,
            r'(?<=Number of Latency one-way Samples: )' + re_int,
            r'(?<=Destination Latency one way Min/Avg/Max: )' + re_int3,
            r'(?<=Source Latency one way Min/Avg/Max: )' + re_int3,
            r'(?<=Number of SD Jitter Samples: )' + re_int,
            r'(?<=Source to Destination Jitter Min/Avg/Max: )' + re_int3,
            r'(?<=Number of DS Jitter Samples: )' + re_int,
            r'(?<=Destination to Source Jitter Min/Avg/Max: )' + re_int3,
            r'(?<=Number Of RTT Over Threshold: )(\d+) \((\d+)%\)',
            r'(?<=Loss Source to Destination: )' + re_int,
            r'(?<=Destination Loss Periods Number: )' + re_int,
            r'(?<=Destination Loss Period Length Min/Max: )' + re_int2,
            r'(?<=Destination Inter Loss Period Length Min/Max: )' + re_int2,
            r'(?<=Loss Destination to Source: )' + re_int,
            r'(?<=Source Loss Periods Number: )' + re_int,
            r'(?<=Source Loss Period Length Min/Max: )' + re_int2,
            r'(?<=Source Inter Loss Period Length Min/Max: )' + re_int2,
            r'(?<=Out Of Sequence: )' + re_int,
            r'(?<=Tail Drop: )' + re_int,
            r'(?<=Packet Late Arrival: )' + re_int,
            r'(?<=Packet Skipped: )' + re_int,
            r'(?<=Planning Impairment Factor \(ICPIF\): )' + re_int,
            r'(?<=MOS score: )' + re_float,
            r'(?<=MinOfMOS: )' + re_float,
            r'(?<=MaxOfMOS: )' + re_float,
            r'(?<=MinOfICPIF: )' + re_int,
            r'(?<=MaxOfICPIF: )' + re_int
        ]

        # List of key names for the returned hash
        # Values must be strings or lists of strings
        key_list = [
            'rtt_cnt',
            ['rtt_min', 'rtt_avg', 'rtt_max'],
            'lat_cnt',
            ['lat_sd_min', 'lat_sd_avg', 'lat_sd_max'],
            ['lat_ds_min', 'lat_ds_avg', 'lat_ds_max'],
            'jit_sd_cnt',
            ['jit_sd_min', 'jit_sd_avg', 'jit_sd_max'],
            'jit_ds_cnt',
            ['jit_ds_min', 'jit_ds_avg', 'jit_ds_max'],
            ['rtt_ovthr', 'rtt_ovthp'],
            'los_sd',
            'los_sd_per',
            ['los_sd_pmin', 'los_sd_pmax'],
            ['los_sd_imin', 'los_sd_imax'],
            'los_ds',
            'los_ds_per',
            ['los_ds_pmin', 'los_ds_pmax'],
            ['los_ds_imin', 'los_ds_imax'],
            'pkt_ooseq',
            'pkt_tdrop',
            'pkt_late',
            'pkt_skip',
            'voc_icpif',
            'voc_mos',
            'voc_mos_min',
            'voc_mos_max',
            'voc_icpif_min',
            'voc_icpif_max'
        ]

        # Ensure the two lists have the same length
        if len(key_list) != len(re_list):
            raise ValueError('lists not same length')

        # Initialize the hash to return
        stats_hash = {}

        # Iterate over the regex and key list in parallel
        for regex, key in zip(re_list, key_list):

            # Perform the regex match against IOS SLA output test
            re_search = re.search(regex, text)

            # For lists, iterate over the list of values and parse
            # These values are always integers, never floats (or should be)
            if isinstance(key, list):
                for sub_key, i in zip(key, range(1, len(key) + 1)):
                    if isinstance(sub_key, str):
                        if re_search:
                            val = FilterModule._try_int(re_search.group(i))
                        else:
                            val = -1
                        #print("adding k:v :: {0}:{1}".format(sub_key,val))
                        stats_hash.update({sub_key: val})

            # For strings, parse the single value
            # Could be int or float (MOS), but don't parse the float.
            # Better to leave it as a nice string rather than imperfect float
            elif isinstance(key, str):
                if re_search:
                    val = FilterModule._try_int(re_search.group())
                else:
                    val = -1
                #print("adding k:v {0}:{1}".format(key,val))
                stats_hash.update({key: val})
            # For invalid data types, do nothing, and loop again

        # Return the hash containing parsed data
        return stats_hash

    @staticmethod
    def ios_ipsla_csv(stats_hash, brief=True):
        '''
        This filter converts a stats_hash (generated by the ios_ipsla_stats
        filter) and writes it to a CSV string. This is useful for printing
        to spreadsheet rollups which contain the output from many probes.
        '''

        # Ensure input is a dict before continuing
        if not isinstance(stats_hash, dict):
            return False

        # Define the sequence of values in the CSV string
        # ... varies depending on verbosity needed
        if brief:
            key_sequence = [
                'rtt_cnt', 'rtt_avg',
                'lat_cnt', 'lat_sd_avg', 'lat_ds_avg',
                'jit_sd_cnt', 'jit_sd_avg',
                'jit_ds_cnt', 'jit_ds_avg',
                'los_sd', 'los_ds',
                'voc_mos'
            ]

        else:
            key_sequence = [
                'rtt_cnt', 'rtt_min', 'rtt_avg', 'rtt_max',
                'rtt_ovthr', 'rtt_ovthp',
                'lat_cnt', 'lat_sd_min', 'lat_sd_avg', 'lat_sd_max',
                'lat_ds_min', 'lat_ds_avg', 'lat_ds_max',
                'jit_sd_cnt', 'jit_sd_min', 'jit_sd_avg', 'jit_sd_max',
                'jit_ds_cnt', 'jit_ds_min', 'jit_ds_avg', 'jit_ds_max',
                'los_sd', 'los_sd_per', 'los_sd_pmin', 'los_sd_pmax',
                'los_sd_imin', 'los_sd_imax',
                'los_ds', 'los_ds_per', 'los_ds_pmin', 'los_ds_pmax',
                'los_ds_imin', 'los_ds_imax',
                'pkt_ooseq', 'pkt_tdrop', 'pkt_late', 'pkt_skip',
                'voc_mos_min', 'voc_mos_max',
                'voc_icpif_min', 'voc_icpif_max'
            ]

        # Write values to the string in sequence
        csv_str = ''
        for key in key_sequence:
            csv_str += str(stats_hash[key]) + ','

        # Trim the trailing comma and return the CSV string
        return csv_str[:-1]

    @staticmethod
    def perf_synopsis(stats_hash, lspv_str="",
                      mtu_ok=False, lspv_success_n=4):
        '''
        This filter is applied to an existing ios_ipsla_stats hash and
        returns a brief explanation of the results. The LSPV code string
        can optionally be passed in. When this optional parameter is not
        included, MPLS connectivity is assumed to not exist. Filter will
        return False when the stats_hash is None (error condition).
        '''

        if stats_hash is None:
            return False

        # Success defined when success is greater than 80%
        lspv_ok = lspv_str.count('!') >= lspv_success_n

        # Success defined when the RTT count is greater than 0
        # 0 means the probe ran but nothing completed
        # -1 means the system failed to collect any output
        ipsla_ok = int(stats_hash['rtt_cnt']) > 0

        # Most common case, so it is processed first
        # Everything succeeded, so return OK
        if ipsla_ok and mtu_ok and lspv_ok:
            return "OK"

        # At least one issue exists. Construct a string
        # to detail what went wrong
        issues = "Issues:"
        if not ipsla_ok:
            issues += " IPSLA stats collection."
        if not mtu_ok:
            issues += " MTU/frag test."
        if not lspv_ok:
            issues += " MPLS LSPs broken."

        return issues

    @staticmethod
    def _get_sla_group(host, groups):
        '''
        This function finds an inventory group corresponding to a host. Checks
        all the groups to see if a host is contained in that group. Given that
        this search is SLA specific, a host should only be in one group, so
        the function returns immediately upon the first match. False is
        returned if the host is not found in any group, which is considered
        to be an error case.
        '''
        # Iterate over all group names
        for key in groups.keys():
            # If the group is a PER group
            if 'ios_per_' in key:
                #print('checking key ' + key)
                # Iterate over each host in the group list
                for s in groups[key]:
                    # Check to see if the host is in a given group
                    if host.upper() == s:
                        #print('{0} is in group {1}'.format(host, key))
                        return key

        #print('{0} not found in any group'.format(host))
        return False

    @staticmethod
    def get_sla(sla, groups, targets):
        '''
        This function returns a list of SLA values for all hosts in the
        target list. The returned list is considered to be parallel to
        the target list and can be used for parallel iteration. The SLA
        value represents the threshold RTT from the inventory host to
        the specific target as documented in the provider's SLA. If
        a sanity check fails, such as the two lists not having the
        same length after the function's logic is complete, a value
        of False is returned.
        '''
        # Find out what group the target hosts are in
        target_group_list = []
        for t in targets:
            # Find the group for a given target
            tgt_group = FilterModule._get_sla_group(t['hostname'][:-2], groups)
            if not tgt_group:
                return False
            # Add that group to the group list
            target_group_list.append(tgt_group)

        sla_list = []

        # Iterate over target groups, since each one needed
        # to be mapped to a regional SLA
        for t in target_group_list:
            #print( 'getting SLA to group ' + t )
            # iterate over the 4 regional SLA keys
            for key in sla.keys():
                #print ('testing sla ' + key )
                # If the name of the group (eg, ios_per_conus) ends in
                # the name of the key, we've found the right SLA
                if t.endswith(key):
                    #print('group {0} ends with {1}'.format(t,key))
                    sla_list.append(int(sla[key]))
                    continue

        #print(sla_list)

        # Sanity check; target and SLA lists must be same length
        if len(sla_list) != len(targets):
            #print('lists not same length')
            return False

        return sla_list

    @staticmethod
    def ios_ping_stats(text):
        '''
        Parses integers from Cisco ping outputs. A dictionary containing
        6 keys with non-negative integer values is returned:
          pkt_per: Percent complete (0<=v<=100)
          pkt_cmp: Packets completed (0<=v<=pkt_tot)
          pkt_tot: Total packets attempted
          rtt_min: Minimum/best RTT time
          rtt_avg: Average RTT time (rtt_min<=rtt_avg<=rtt_max)
          rtt_max: Maximum/worse RTT time

        There are two forms of input strings. One is a successful case:

        "Success rate is 100 percent (5/5), /
         round-trip min/avg/max = 247/247/248 ms"

        The other is the failed case:

        "Success rate is 0 percent (0/5)"

        The function has many sanity checks to ensure the parsing was
        correct and the integers make sense. Any failure results in
        a return false of False.
        '''
        if text is None or text == "":
            return False

        # Develop regex and find digits
        pattern = r'\d+'
        re_list = re.findall(pattern, text)

        # Parse values to integers
        stats_list = [int(s) for s in re_list]

        # Ping failed; just populate RTT times with 0
        if len(stats_list) == 3:
            stats_list.extend([0, 0, 0])

        # Sanity check; length must be 6
        if len(stats_list) != 6:
            return False

        # Construct dictionary of parsed values
        cp_hash = {
            'pkt_per': stats_list[0],
            'pkt_cmp': stats_list[1],
            'pkt_tot': stats_list[2],
            'rtt_min': stats_list[3],
            'rtt_avg': stats_list[4],
            'rtt_max': stats_list[5]
        }

        # Sanity check; percent must be between 0 and 100
        if cp_hash['pkt_per'] < 0 or cp_hash['pkt_per'] > 100:
            return False

        # Sanity check; completed must be between 0 and total
        if cp_hash['pkt_cmp'] < 0 or cp_hash['pkt_cmp'] > cp_hash['pkt_tot']:
            return False

        # Sanity check; average RTT must be between min and max
        if (cp_hash['rtt_avg'] < cp_hash['rtt_min'] or
                cp_hash['rtt_avg'] > cp_hash['rtt_max']):
            return False

        # CSV flag not set; return the dictionary structure
        return cp_hash

    @staticmethod
    def ios_ping_csv(cp_hash):
        '''
        This filter return a string of values in clean CSV format given
        an input of a cisco ping hash (cp_hash) from the previous filter.
        This filter can simplify jinja2 templates, for example.
        The 6 integers are returned in CSV format as a string:
        "pkt_per,pkt_cmp,pkt_tot,rtt_min,rtt_avg,rtt_max"
        '''

        # Return string of values in clean CSV format
        # This can simplify jinja2 templates, for example
        return "{0},{1},{2},{3},{4},{5}".format(
            cp_hash['pkt_per'], cp_hash['pkt_cmp'], cp_hash['pkt_tot'],
            cp_hash['rtt_min'], cp_hash['rtt_avg'], cp_hash['rtt_max'])

    @staticmethod
    def ios_parse_ip(text):
        '''
        The function is a stopgap for the ios_facts module which in 2.4.x
        unreliably captures IP addresses due to an intermittent bug. The
        input text should look like the text below, and a hash is returned
        contained the full ipv4/mask string, and each independent variables
        as separate strings.
          ROUTER#show ip interface Loopback | include Internet_address
           Internet address is 10.108.0.50/32
        '''
        # Perform sanity check for valid input
        if not text:
            return False
        # Define regex and perform search
        octet_str = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
        regex = r'(?<=Internet address is )({0})/(\d+)'.format(octet_str)
        re_search = re.search(regex, text)
        if re_search:
            try:
                socket.inet_aton(re_search.group(1))
                ip_hash = {
                    "full_str": re_search.group(0),
                    "address": re_search.group(1),
                    "subnet": int(re_search.group(2))
                }
                #print(ip_hash)
                return ip_hash
            except socket.error:
                return False
        else:
            return False

