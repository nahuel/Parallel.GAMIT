"""
Project: Parallel.GAMIT
Date: 7/15/20 5:25 PM
Author: Demian D. Gomez

"""

import os
import re

# app
from pyDate import Date
from pyEvents import Event

TYPE_CRINEZ = 0
TYPE_RINEX  = 1
TYPE_RINEZ  = 2
TYPE_CRINEX = 3
TYPE_CRINEZ_2 = 4

version_2_ext = {TYPE_CRINEZ  : 'd.Z',
                 TYPE_RINEX   : 'o',
                 TYPE_RINEZ   : 'o.Z',
                 TYPE_CRINEX  : 'd',
                 TYPE_CRINEZ_2: 'd.gz'}  # some newer files come in d.gz

version_3_ext = {TYPE_CRINEZ : 'crx.gz',
                 TYPE_RINEX  : 'rnx',
                 TYPE_RINEZ  : 'rnx.gz',
                 TYPE_CRINEX : 'crx'}


def check_year(year):
    # to check for wrong dates in RinSum
    year = int(year)

    if year - 1900 < 80 and year >= 1900:
        return year - 1900 + 2000

    elif year < 1900 and year >= 80:
        return year + 1900

    elif year < 1900 and year < 80:
        return year + 2000

    return year


class RinexNameException(Exception):
    def __init__(self, value):
        self.value = value
        self.event = Event(Description=value, EventType='error')

    def __str__(self):
        return str(self.value)


class RinexNameFormat(object):
    def __init__(self, filename):
        self.path     = os.path.dirname(filename)
        self.filename = os.path.basename(filename)
        self.version  = 0

        self.type = self.identify_rinex_type(filename)

        parts = self.split_filename(filename)
        try:
            if self.version < 3:
                self.StationCode        = parts[0]
                self.monument           = None
                self.receiver           = None
                self.country            = None
                self.doy                = parts[1]
                self.session            = parts[2]
                self.year               = parts[3]
                self.format_compression = parts[4]
                self.start_time         = None
                self.data_source        = None
                self.file_period        = None
                self.data_frequency     = None
                self.data_type          = None
                self.date               = Date(year=check_year(self.year), doy=int(self.doy))
            else:
                # DDG: lowercase station code to match the default station name conventions
                self.StationCode        = parts[0][0:4].lower()
                self.monument           = parts[0][4:5]
                self.receiver           = parts[0][5:6]
                self.country            = parts[0][6:]
                self.session            = None
                self.year               = parts[2][0:4]
                self.doy                = parts[2][4:7]
                self.format_compression = parts[6]
                self.start_time         = parts[2]
                self.data_source        = parts[1]
                self.file_period        = parts[3]
                self.data_frequency     = parts[4]
                self.data_type          = parts[5]
                self.date               = Date(year=int(self.year), doy=int(self.doy))

            self.month = self.date.month
            self.day   = self.date.day

        except Exception as e:
            raise RinexNameException(e)

    def identify_rinex_type(self, filename):

        # get the type of file passed
        filename = os.path.basename(filename)

        ft = next((t for t, ext in version_2_ext.items()
                   if filename.endswith(ext)),
                  None)

        if ft is not None:
            self.version = 2
            return ft
            # @todo after return exception, this was never raised, remove it?
            # raise RinexNameException('Invalid filename format: ' + filename)
        else:
            self.version = 3

            # DDG: identify file type from filename
            sfile = re.findall(r'[A-Z0-9]{9}_[RSU]_[0-9]{11}_[0-9]{2}[MHDYU]_[0-9]{2}[CZSMHDU]_'
                               r'[GREJCISM][OMN]\.(crx|rnx)(.gz|.zip|.bzip2|.bz2)?$', filename)
            if not sfile:
                raise RinexNameException('Could not determine the rinex type (malformed filename): ' + filename)
            elif sfile[0][0] == 'rnx':
                return (TYPE_RINEX if sfile[0][1] is '' else
                        TYPE_RINEZ)
            elif sfile[0][0] == 'crx':
                return (TYPE_CRINEX if sfile[0][1] is '' else
                        TYPE_CRINEZ)
            
            # @todo must raise RinexNameException here?

    def filename_base(self):
        if self.version < 3:
            return self.StationCode + self.doy + self.session + '.' + self.year
        else:
            return self.StationCode.upper() + self.monument + self.receiver + self.country + '_' + \
                   self.data_source + '_' + self.start_time + '_' + self.file_period + '_' + \
                   self.data_frequency + '_' + self.data_type

    def to_rinex_format(self, to_type, no_path=False):
        # join the path to the file again
        return os.path.join('' if no_path else self.path,
                            self.filename_base() + (version_2_ext[to_type]
                                                    if self.version < 3 else
                                                    '.' + version_3_ext[to_type]))

    def filename_no_ext(self, no_path=False):
        # join the path to the file again
        return os.path.join('' if no_path else self.path,
                            self.filename_base())

    def split_filename(self, filename):

        if self.version < 3:
            sfile = re.findall(r'(\w{4})(\d{3})(\w)\.(\d{2})([doOD](?:.gz|.Z)?)$', filename)

            if sfile:
                return sfile[0]
            else:
                raise RinexNameException('Invalid filename format: %s for rinex version %s' %
                                         (filename, str(self.version)))
        else:
            sfile = re.findall(r'([A-Z0-9]{9})_([RSU])_([0-9]{11})_([0-9]{2}[MHDYU])_([0-9]{2}[CZSMHDU])_'
                               r'([GREJCISM][OMN])\.((?:crx|rnx)(?:.gz|.zip|.bzip2|.bz2)?)$', filename)
            if sfile:
                return sfile[0]
            else:
                raise RinexNameException(
                    'Invalid filename format: ' + filename + ' for rinex version ' + str(self.version))
