#!/usr/bin/python
# vim: set fileencoding=utf-8 :
""" Unittests for copy_duplicity_backups """
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

# Standard library imports
import datetime
import os
import shutil
import unittest
import tempfile

# Module to test
import copy_duplicity_backups

class TestNameGenerator():
    '''Helper class for tests
    Generates names for files'''

    def __init__(self):
        self.last_timestamp_object = None
    
    def gen_names(self, inc_full, year, month, day, nr_vols):
        '''Generates a list of file names for a backup run

        For incremental backups the first timestamp is automatically
        set to the last backup.

        Args:
            inc_full: Either "full" or "inc"
            year: numerical year of backup
            month: numerical month of backup
            nr_vols: number of volumes

        Returns:
            list of Strings.
            '''
        datetime_format = "%Y%m%dT%H%M%SZ"
        assert inc_full == "inc" or inc_full == "full" 

        timestamp_object = datetime.datetime(year, month, day)
        timestamp = timestamp_object.strftime(datetime_format)
        manifest = ""
        signatures = ""
        vols = []

        if inc_full == "full":
            manifest = "duplicity-full." + timestamp + ".manifest.gpg"
            signatures = ( "duplicity-full-signatures.%s.sigtar.gpg" %
                (timestamp) )
            for i in range(1, nr_vols + 1):
                vols.append( "duplicity-full.%s.vol%d.difftar.gpg" %
                        (timestamp, i) )
        else:
            last_timestamp = (
                self.last_timestamp_object.strftime(datetime_format) )
            manifest = ( "duplicity-inc.%s.to.%s.manifest.gpg" % 
                            ( last_timestamp, timestamp) )
            signatures = ( "duplicity-new-signatures.%s.to.%s.sigtar.gpg" %
                ( last_timestamp, timestamp) )
            for i in range(1, nr_vols + 1):
                vols.append(
                        "duplicity-inc.%s.to.%s.vol%d.difftar.gpg" %
                        ( last_timestamp, timestamp, i ) )
                
        self.last_timestamp_object = timestamp_object
        result = vols
        result.append(signatures)
        result.append(manifest)
        return result


class TestAll(unittest.TestCase):
    '''Test of the module in general'''

    @staticmethod
    def gen_tempfolder():
        '''Returns temporary folder name'''
        return tempfile.mkdtemp(prefix="tmp_copy_duplicity_backups")

    @staticmethod
    def add_files(folder, filenames):
        '''Adds an empty filename to folder '''
        for filename in filenames:
            path = os.path.join(folder, filename)
            with open(path, mode="wb"):
                pass



    def test_01(self):
        '''Only one full'''
        folder = self.gen_tempfolder()
        names_in = [
                "duplicity-full.20130101T010000Z.manifest.gpg",
                "duplicity-full.20130101T010000Z.vol1.difftar.gpg",
                "duplicity-full.20130101T010000Z.vol2.difftar.gpg",
                "duplicity-full-signatures.20130101T010000Z.sigtar.gpg"
                ]
        self.add_files(folder, names_in)
        result = copy_duplicity_backups.return_last_n_full_backups(folder, 3)
        self.assertEqual(sorted(names_in), sorted(result))

        shutil.rmtree(folder)
    
    def test_02(self):
        '''One full and old incs from previous backup'''
        folder = self.gen_tempfolder()
        old_leftover = [
"duplicity-inc.20130101T000000Z.to.20130101T000001Z.manifest.gpg",
"duplicity-inc.20130101T000000Z.to.20130101T000001Z.vol1.difftar.gpg",
"duplicity-new-signatures.20130101T010000Z.to.20130101T000001Z.sigtar.gpg"
                ]
        last_full = [
"duplicity-full.20130101T010000Z.manifest.gpg",
"duplicity-full.20130101T010000Z.vol1.difftar.gpg",
"duplicity-full.20130101T010000Z.vol2.difftar.gpg",
"duplicity-full-signatures.20130101T010000Z.sigtar.gpg"
                ]
        names_in = old_leftover + last_full
        self.add_files(folder, names_in)

        result = copy_duplicity_backups.return_last_n_full_backups(folder, 1)
        self.assertEqual(sorted(last_full), sorted(result))

        shutil.rmtree(folder)

    def test_03(self):
        '''Full with incs and one old inc'''
        folder = self.gen_tempfolder()
        old_leftover = [
"duplicity-inc.20130101T000000Z.to.20130101T000001Z.manifest.gpg",
"duplicity-inc.20130101T000000Z.to.20130101T000001Z.vol1.difftar.gpg",
"duplicity-new-signatures.20130101T010000Z.to.20130101T000001Z.sigtar.gpg"
                ]
        last_full = [
"duplicity-full.20130101T010000Z.manifest.gpg",
"duplicity-full.20130101T010000Z.vol1.difftar.gpg",
"duplicity-full.20130101T010000Z.vol2.difftar.gpg",
"duplicity-full-signatures.20130101T010000Z.sigtar.gpg"
                ]
        after_full = [
"duplicity-inc.20130101T010000Z.to.20130102T010001Z.manifest.gpg",
"duplicity-inc.20130101T010000Z.to.20130102T010001Z.vol1.difftar.gpg",
"duplicity-new-signatures.20130101T010000Z.to.20130102T010001Z.sigtar.gpg",
"duplicity-inc.20130102T010001Z.to.20130103T010000Z.manifest.gpg",
"duplicity-inc.20130102T010001Z.to.20130103T010000Z.vol1.difftar.gpg",
"duplicity-new-signatures.20130102T010001Z.to.20130103T010000Z.sigtar.gpg"
                ]
        names_in = old_leftover + last_full + after_full
        self.add_files(folder, names_in)

        result = copy_duplicity_backups.return_last_n_full_backups(folder, 1)
        self.assertEqual(sorted(last_full+after_full), sorted(result))

        shutil.rmtree(folder)


    def test_04(self):
        '''3 fulls with incs, select last 2 fulls'''

        gen = TestNameGenerator()

        full_1 = gen.gen_names("full", 2013, 1, 1, 8)
        incs_1 = (
            gen.gen_names("inc", 2013, 1, 2, 1) +
            gen.gen_names("inc", 2013, 1, 3, 1) +
            gen.gen_names("inc", 2013, 1, 4, 2) +
            gen.gen_names("inc", 2013, 1, 6, 1) )

        full_2 = gen.gen_names("full", 2013, 1, 8, 1)
        incs_2 = (
            gen.gen_names("inc", 2013, 1, 9, 3) +
            gen.gen_names("inc", 2013, 1, 10, 4) +
            gen.gen_names("inc", 2013, 1, 11, 2) )

        full_3 = gen.gen_names("full", 2013, 2, 1, 1)
        incs_3 = (
            gen.gen_names("inc", 2013, 2, 3, 2) +
            gen.gen_names("inc", 2013, 2, 4, 20) )


        names_in = full_1 + incs_1 + full_2 + incs_2 + full_3 + incs_3

        folder = self.gen_tempfolder()
        self.add_files(folder, names_in)

        result = copy_duplicity_backups.return_last_n_full_backups(folder, 2)
        expected = full_2 + incs_2 + full_3 + incs_3

        self.assertEqual(sorted(result), sorted(expected))

        shutil.rmtree(folder)


    def test_05(self):
        '''Multi regex match'''
        folder = self.gen_tempfolder()
        # Multiple matches for a wrong file,
        # "^" / "$"  in regex necessary
        names_in = [
                "duplicity-full.20130101T010000Z.manifest.gpg",
                "duplicity-full.20130101T010000Z.vol1.difftar.gpg"
                "duplicity-full.20130101T010000Z.vol2.difftar.gpg"
                "duplicity-full-signatures.20130101T010000Z.sigtar.gpg"
                ]

        self.add_files(folder, names_in)

        with self.assertRaises(copy_duplicity_backups.UnknownFileException):
            copy_duplicity_backups.return_last_n_full_backups(folder, 3)


        shutil.rmtree(folder)

