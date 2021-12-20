#!/usr/bin/python3

import os
import shutil
import sys

from tesseract_cache import tesseract_cache


def tesseract_cli_wrapper(argv,
                          cache_dir='/var/cache/tesseract',
                          verbose=True):
    """Wrapper for tesseract command line interface

    if result output file in cache, copy from cache, else return fake
    OCR result with status
    """

    if os.getenv('TESSERACT_CACHE_DIR'):
        cache_dir = os.getenv('TESSERACT_CACHE_DIR')

    (input_filename, tesseract_configfilename,
     cache_filename) = tesseract_cache.parse_tesseract_parameters(argv)

    output_filename = argv[2] + '.' + tesseract_configfilename

    cache_file_path = os.path.join(cache_dir, cache_filename)
    if os.path.isfile(cache_file_path):
        if verbose:
            print("Copying OCR result for content of {} from cache {}".format(
                input_filename, cache_filename))
        # copy cached result to output filename
        shutil.copy(cache_file_path, output_filename)
        return 0
    if verbose:
        print("OCR result not in cache, writing fake OCR"
              " result with status info to {}".format(
                  output_filename))

    with open(output_filename, 'w') as textfile:
        textfile.write('[Image (no OCR yet)]')

    return 0


#
# If started by command line (not imported for functions) get command line
# parameters and start OCR
#

if __name__ == "__main__":

    # copy OCR result from cache or run OCR by Tesseract
    result_code = tesseract_cli_wrapper(sys.argv)

    sys.exit(result_code)
