#!/usr/bin/python3

"""Tesseract cache
so once processed OCR results can be read from cache

Python library:
If used as library in python software by import, you can use get_ocr_text() to
start OCR and get the text

CLI wrapper
If used as tesseract command line interface (calling __main__) the wrapper
function tesseract_cli_wrapper() is used
"""

import hashlib
import os
import shutil
import sys
import subprocess
import tempfile
import codecs
import glob
import logging
from typing import Optional

logger = logging.getLogger("tesseract_cache")


def get_cache_filename(filename,
                       lang,
                       options,
                       tesseract_configfilename='txt'):
    """calc filename in cache dir by file content and tesseract
    options (hashes),
    not filename so cache will be used, too if multiple files of the same image
    and if using temporary filenames like Tika-Server
    """

    # hash of file content
    with open(filename, 'rb') as imagefile:
        hash_filecontent = hashlib.sha256(imagefile.read()).hexdigest()

    hash_options = hashlib.md5(options.encode('utf8')).hexdigest()

    cache_filename = (lang + '-' + hash_filecontent + '-' + hash_options +
                      '.' + tesseract_configfilename)

    return cache_filename


def get_ocr_text(filename,
                 lang='eng',
                 cache_dir='/var/cache/tesseract'):
    """Get text from image

    If enabled cache and text available in cache, read from cache,
    else do OCR and write to cache
    """

    text = ''
    ocr_filename = None
    options = '-l ' + lang

    if not lang:
        lang = 'eng'

    if os.getenv('TESSERACT_CACHE_DIR'):
        cache_dir = os.getenv('TESSERACT_CACHE_DIR')

    if cache_dir:
        # cache dir configured, so get cache file name
        ocr_filename = get_cache_filename_multilang(
            filename=filename, lang=lang,
            options=options, cache_dir=cache_dir)
        output_filename = os.path.join(cache_dir, 'temp-' + str(os.getpid()) +
                                       '-' + os.path.basename(ocr_filename))
        try:
            text = readfile(ocr_filename)
            logger.debug("Using OCR result for content of %s from cache %s",
                         filename, ocr_filename)
            return text
        except FileNotFoundError:
            pass
    else:
        # calc tempfilename from temp dir, process id and filename
        md5hash = hashlib.md5(filename.encode('utf-8')).hexdigest()
        output_filename = os.path.join(
            tempfile.gettempdir(),
            "opensemanticetl_ocr_" + str(os.getpid()) + md5hash)
        ocr_filename = output_filename + '.txt'

    argv = ['tesseract',
            filename,
            output_filename,
            '-l', lang,
            '--user-words', '/etc/opensemanticsearch/ocr/dictionary.txt'
            ]

    if cache_dir:
        logger.debug("OCR result not in cache, running"
                     " Tesseract OCR by arguments %s",
                     argv)

    # run tesseract
    result_code = subprocess.call(argv)

    if result_code != 0:
        text = "Error: OCR failed for {}\n".format(filename)
        sys.stderr.write(text)

    # move temporary filename to cache filename
    if cache_dir:
        os.rename(output_filename + '.txt', ocr_filename)

    try:
        text = readfile(ocr_filename)
    except FileNotFoundError:
        pass
    # delete temporary OCR result file if no cache configured
    if not cache_dir:
        os.remove(ocr_filename)

    return text


def readfile(filename) -> Optional[str]:
    """read text from OCR result file"""
    with codecs.open(filename, "r", encoding="utf-8") as ocr_file:
        text = ocr_file.read()

    logger.debug("Characters recognized: %s", len(text))

    return text


def get_cache_filename_multilang(filename: str,
                                 cache_dir: str,
                                 options: str,
                                 lang: str = 'eng') -> str:
    suffix = get_cache_filename(filename, lang="", options=options)
    required_langs = frozenset(lang.split('+')) if lang else frozenset()
    cache_candidates = glob.iglob(os.path.join(
        cache_dir, "*" + suffix))

    def provided_langs(candidate):
        return frozenset(os.path.basename(
            candidate).split('-', 1)[0].split('+'))
    # Find candidates providing all required langs:
    matching_candidates = (
        candidate for candidate in cache_candidates
        if required_langs.issubset(
            provided_langs(candidate)
        )
    )
    # Take the candidate with the shortest filename
    # (this will contain the minimal amount of not required langs):
    ocr_cache_filename = min(matching_candidates, key=len, default=None)
    # Fall back to a naive file name:
    return ocr_cache_filename or os.path.join(cache_dir, lang + suffix)


def parse_tesseract_parameters(argv):
    """Parse the parameters of tesseract cli wrapper call
    and return filename, options and cache filename
    """

    input_filename = argv[1]

    tesseract_configfilename = 'txt'
    if argv[-1] in ['txt', 'hocr', 'pdf']:
        tesseract_configfilename = argv[-1]

    lang = 'eng'
    if '-l' in argv:
        lang = argv[argv.index('-l') + 1]
        logger.debug("Using Tesseract OCR language parameter: %s", lang)

    #
    # calc filename in cache dir by file content and options (hash),
    # not filename
    # so cache will be used, too for temprorary filenames and if multiple
    # files of the same image
    #

    # hash of options (without the changing (temp) file names)
    options = '-l ' + lang

    if len(argv) > 3:
        options = ' '.join(argv[3:])

    cache_filename = get_cache_filename(
        filename=input_filename, lang=lang,
        tesseract_configfilename=tesseract_configfilename,
        options=options)

    return input_filename, tesseract_configfilename, cache_filename


def tesseract_cli_wrapper(argv,
                          cache_dir='/var/cache/tesseract'):
    """Wrapper for tesseract command line interface

    if result output file in cache, copy from cache, else run tesseract
    and copy to cache
    """

    if os.getenv('TESSERACT_CACHE_DIR'):
        cache_dir = os.getenv('TESSERACT_CACHE_DIR')

    (input_filename, tesseract_configfilename,
     cache_filename) = parse_tesseract_parameters(argv)
    cache_filepath = os.path.join(cache_dir, cache_filename)

    output_filename = argv[2] + '.' + tesseract_configfilename

    if os.path.isfile(cache_filepath):
        logger.debug("Copying OCR result for content of %s from cache %s",
                     input_filename, cache_filename)
        # copy cached result to output filename
        shutil.copy(cache_filepath, output_filename)
        return 0

    logger.debug("OCR result not in cache, running "
                 "Tesseract OCR by arguments %s", argv)

    # run tesseract and copy output file to cache
    result_code = subprocess.call(argv)

    logger.debug("Copying OCR result %s to cache %s",
                 output_filename, cache_dir + cache_filename)

    shutil.copy(output_filename, cache_filepath)

    return result_code


#
# If started by command line (not imported for functions)
# get command line parameters and start OCR
#

if __name__ == "__main__":

    # read command line parameters
    _argv = sys.argv
    # since running on command line instead being used as Python library
    # the option argv[0] is not tesseract command but this wrapper
    # so change in new argv for OCR the command parameter to real tesseract
    _argv[0] = 'tesseract'

    # copy OCR result from cache or run OCR by Tesseract
    sys.exit(tesseract_cli_wrapper(_argv))
