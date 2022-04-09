import os
import socket
import numpy as np

"""
    refer:
     Tracker List - https://github.com/ngosang/trackerslist
"""

dht_bootstrap_address = [
    # dht nodes
    ('router.utorrent.com', 6881),
    ('router.bittorrent.com', 6881),
    ('dht.transmissionbt.com', 6881),
    ('dht.aelitis.com', 6881),
    # ('router.silotis.us', 6881),
    ('dht.libtorrent.org', 25401),
    ('dht.anacrolix.link', 42069),
    ('router.bittorrent.cloud', 42069),

    # # trackers
    # ('tracker.opentrackr.org', '1337'),
    # ('open.tracker.cl', '1337'),
    # ('9.rarbg.com', '2810'),
    # ('pow7.com', '80'),
    # ('tracker.openbittorrent.com', '6969'),
    # ('tracker.openbittorrent.com', '80'),
    # ('www.torrent.eu.org', '451'),
    # ('tracker.torrent.eu.org', '451'),
    # ('open.stealth.si', '80'),
    # ('exodus.desync.com', '6969'),
    # ('ipv4.tracker.harry.lu', '80'),
    # ('opentor.org', '2710'),
    # ('tracker.tiny-vps.com', '6969'),
    # ('tracker.dler.org', '6969'),
    # ('tracker.moeking.me', '6969'),
    # ('explodie.org', '6969'),
    # ('tr.torland.ga', '443'),
    # ('vps02.net.orel.ru', '80'),
    # ('vibe.sleepyinternetfun.xyz', '1738'),
    # ('u4.trakx.crim.ist', '1337'),
]

# get real ip address
for i, ele in enumerate(dht_bootstrap_address):
    ip, port = socket.getaddrinfo(*ele)[0][-1]
    dht_bootstrap_address[i] = (ip, port)

# # 21/04/04
# bootstrap_nodes_filename = os.path.join(os.path.dirname(__file__), 'bootstrap_nodes.csv')
# extra_dht_address = np.loadtxt(bootstrap_nodes_filename, dtype=str, delimiter=',')
# extra_dht_address = [tuple([x[0], int(x[1])]) for x in extra_dht_address]
#
# dht_bootstrap_address.extend(extra_dht_address)
# dht_bootstrap_address = list(set(dht_bootstrap_address))


ONE_DAY = 3600 * 24
ONE_WEEK = ONE_DAY * 7

#
# def add_bootstrap_nodes(*nodes):
#     global dht_bootstrap_address
#
#     with open(bootstrap_nodes_filename, 'a') as fp:
#         lines = [','.join([str(a) for a in x]) + '\n' for x in nodes]
#         fp.writelines(lines)
#     dht_bootstrap_address.extend([tuple(x) for x in nodes])


DEFAULT_KRPC_CONFIG = {
    'address': ('0.0.0.0', 6881),
    'root_node': None,
    'logger': 'krpc',
}

DEFAULT_BIT_TORRENT_CONFIG = {
    'address': ('0.0.0.0', 6882),
    'root_node': None,
    'logger': 'bt',
}

