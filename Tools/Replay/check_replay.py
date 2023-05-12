#!/usr/bin/env python

'''
check that replay produced identical results
'''

from __future__ import print_function

def check_log(logfile, progress=print, ekf2_only=False, ekf3_only=False, verbose=False):
    '''check replay log for matching output'''
    from pymavlink import mavutil
    progress(f"Processing log {logfile}")
    failure = 0
    errors = 0
    count = 0
    base_count = 0
    counts = {}
    base_counts = {}

    mlog = mavutil.mavlink_connection(logfile)

    ek2_list = ['NKF1','NKF2','NKF3','NKF4','NKF5','NKF0','NKQ', 'NKY0', 'NKY1']
    ek3_list = ['XKF1','XKF2','XKF3','XKF4','XKF0','XKFS','XKQ','XKFD','XKV1','XKV2','XKY0','XKY1']

    if ekf2_only:
        mlist = ek2_list
    elif ekf3_only:
        mlist = ek3_list
    else:
        mlist = ek2_list + ek3_list

    base = {m: {} for m in mlist}
    while True:
        m = mlog.recv_match(type=mlist)
        if m is None:
            break
        if not hasattr(m,'C'):
            continue
        mtype = m.get_type()
        if mtype not in counts:
            counts[mtype] = 0
            base_counts[mtype] = 0
        core = m.C
        if core < 100:
            base[mtype][core] = m
            base_count += 1
            base_counts[mtype] += 1
            continue
        mb = base[mtype][core-100]
        count += 1
        counts[mtype] += 1
        mismatch = False
        for f in m._fieldnames:
            if f == 'C':
                continue
            v1 = getattr(m,f)
            v2 = getattr(mb,f)
            if v1 != v2:
                mismatch = True
                errors += 1
                progress(f"Mismatch in field {mtype}.{f}: {str(v1)} {str(v2)}")
        if mismatch:
            progress(mb)
            progress(m)
    progress("Processed %u/%u messages, %u errors" % (count, base_count, errors))
    if verbose:
        for mtype, value in counts.items():
            progress(
                "%s %u/%u %d"
                % (
                    mtype,
                    value,
                    base_counts[mtype],
                    base_counts[mtype] - counts[mtype],
                )
            )
    if count == 0 or abs(count - base_count) > 100:
        failure += 1
    return failure == 0 and errors == 0

if __name__ == '__main__':
    import sys
    from argparse import ArgumentParser
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--ekf2-only", action='store_true', help="only check EKF2")
    parser.add_argument("--ekf3-only", action='store_true', help="only check EKF3")
    parser.add_argument("--verbose", action='store_true', help="verbose output")
    parser.add_argument("logs", metavar="LOG", nargs="+")

    args = parser.parse_args()

    failed = False
    for filename in args.logs:
        if not check_log(filename, print, args.ekf2_only, args.ekf3_only, args.verbose):
            failed = True

    if failed:
        print("FAILED")
        sys.exit(1)
    print("Passed")
    sys.exit(0)
