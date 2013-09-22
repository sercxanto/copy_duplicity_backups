#!/usr/bin/python
# vim: set fileencoding=utf-8 :
""" report_last_n_full_backups.py
   
    Returns list of last n full duplicity backups"""
#
#   Copyright (C) 2013 Georg Lutz <georg AT NOSPAM georglutz DOT de>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Standard library imports:
import argparse
import datetime
import os
import re
import shutil
import sys
import unittest
import tempfile


def get_args():
    '''Configures command line parser and returns parsed parameters'''
    parser = argparse.ArgumentParser(
            description="Returns list of last n full duplicity backups")
    parser.add_argument("directory", help="Directory to scan")
    parser.add_argument("--nr", help="Number of full backups",
            default=2, type=int)

    return parser.parse_args()


def ts_regex(number):
    '''Returns timestamp regex, matching group with given numberr, e.g.
    "timestamp1" or "timestamp2" '''
    if number != None:
        return "(?P<timestamp" + str(number) + ">\d{8}T\d{2}\d{4}[A-Z])"
    else:
        return "(?P<timestamp>\d{8}T\d{2}\d{4}[A-Z])"


def get_unix_timestamp(timestamp):
    '''Returns a unix timestamp for given textual duplicity timestamp'''
    time = datetime.datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ")
    return (time - datetime.datetime(1970, 1 , 1)).total_seconds()


def add_entry(dup_files, timestamp, is_full, filename):
    '''Adds an entry to the dup_files dictionnary.
    Either a new entry with timestamp is created or an existing is updated.

    Example:

        dup_files = {"123456789" :
            { "is_full": True,
              "files": ["file1", "file2", "file3"] } }

    Raises an exception on error'''

    if dup_files.has_key(timestamp):
        assert dup_files[timestamp]["is_full"] == is_full
        if dup_files[timestamp].has_key("files"):
            dup_files[timestamp]["files"].append(filename)
        else:
            dup_files[timestamp]["files"] = [filename]
    else:
        entry = {}
        entry["is_full"] = is_full
        entry["files"] = [filename]
        dup_files[timestamp] = entry


def get_duplicity_files(directory):
    '''For a given directory returns files which belong to duplicity.

    In case that a file is found not belonging to duplicity an exception
    is raised.

       Duplicity naming scheme:
            duplicity-full.timestamp.manifest.gpg
            duplicity-full.timestamp.volnr.difftar.gpg
            duplicity-full-signatures.timestamp.sigtar.gpg
            duplicity-inc.timestamp1.to.timestamp2.manifest.gpg
            duplicity-inc.timestamp1.to.timestamp2.volnr.difftar.gpg
            duplicity-new-signatures.timestamp1.to.timestamp2.sigtar.gpg
       timestamp example: 20130126T070058Z'''

    full_prefix = "duplicity\-full\." + ts_regex(None) + "\."
    full_manifest = re.compile(full_prefix + "manifest\.gpg")
    full_difftar = re.compile(full_prefix + "vol\d+\.difftar\.gpg")
    full_signatures = re.compile(
            "duplicity\-full-signatures\." + ts_regex(None) + "\.sigtar\.gpg")
    inc_prefix = "duplicity\-inc\." + ts_regex(1) + "\.to\." + ts_regex(2) + "\."
    inc_manifest = re.compile(inc_prefix + "manifest\.gpg")
    inc_difftar = re.compile(inc_prefix + "vol\d+\.difftar\.gpg")
    inc_signatures = re.compile(
            "duplicity\-new\-signatures\." + ts_regex(1) + "\.to\."
            + ts_regex(2) + "\.sigtar\.gpg" )
    
    all_files = os.listdir(directory)
    dup_files = {}
    for name in all_files:
        result = full_manifest.match(name)
        if result != None :
            timestamp = get_unix_timestamp(result.group("timestamp"))
            add_entry(dup_files, timestamp, True, name)
            continue

        result = full_difftar.match(name)
        if result != None:
            timestamp = get_unix_timestamp(result.group("timestamp"))
            add_entry(dup_files, timestamp, True, name)
            continue

        result = full_signatures.match(name)
        if result != None:
            timestamp = get_unix_timestamp(result.group("timestamp"))
            add_entry(dup_files, timestamp, True, name)
            continue
        
        result = inc_manifest.match(name)
        if result != None:
            timestamp = get_unix_timestamp(result.group("timestamp2"))
            add_entry(dup_files, timestamp, False, name)
            continue
        
        result = inc_difftar.match(name)
        if result != None:
            timestamp = get_unix_timestamp(result.group("timestamp2"))
            add_entry(dup_files, timestamp, False, name)
            continue
        
        result = inc_signatures.match(name)
        if result != None:
            timestamp = get_unix_timestamp(result.group("timestamp2"))
            add_entry(dup_files, timestamp, False, name)
            continue

        print "not found!!! " + name
        raise Exception ("spam", "eggs")
    return dup_files


def return_last_n_full_backups(directory, nr_full):
    '''Returns list of duplicity files last n full backups into the past'''
    dup_files = get_duplicity_files(directory)
    result = []
    counter = 0
    for key in sorted(dup_files.iterkeys(), reverse=True):
        if dup_files[key]["is_full"]:
            counter = counter + 1
        if counter <= nr_full:
            result = result + dup_files[key]["files"]
        else:
            break
    return result



def main():
    '''main function, called when script file is executed directly'''
    args = get_args()
    if not os.path.isdir(args.directory):
        print >> sys.stderr, "Directory not found"
        sys.exit(1)

    files = return_last_n_full_backups(args.directory, args.nr)
    for file_ in sorted(files):
        print file_


if __name__ == "__main__":
    main()



class TestAll(unittest.TestCase):
    '''Test of the module in general'''

    @staticmethod
    def gen_tempfolder():
        '''Returns temporary folder name'''
        return tempfile.mkdtemp(prefix="tmp_report_last_n")

    @staticmethod
    def add_file(folder, filenames):
        '''Adds an empty filename to folder '''
        for filename in filenames:
            path = os.path.join(folder, filename)
            with open(path, mode="wb"):
                pass

    def test_01(self):
        '''Dummy test'''
        folder = self.gen_tempfolder()
        names = [ "duplicity-full.20130101T010000Z.manifest.gpg" ]
        
        self.add_file(folder, names)

        shutil.rmtree(folder)

