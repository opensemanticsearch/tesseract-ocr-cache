#!/usr/bin/python3

import hashlib
import os
import shutil
import sys
import subprocess

def tesseract_ocr(argv, cache_dir='/var/cache/tesseract', verbose=True):
    
    if os.getenv('TESSERACT_CACHE_DIR'):
        cache_dir = os.getenv('TESSERACT_CACHE_DIR')

    if not cache_dir.endswith(os.path.sep):
        cache_dir += os.path.sep

    input_filename = argv[1]
        
    if not os.path.isfile(input_filename):
    
        # first argument not a filename, so
        # just pass all arguments to tesseract without using cache
        result = subprocess.call(argv)
        return result
    
    else:
        #
        # if in cache, copy result from cache, else run tesseract and copy to cache
        #
        
        tesseract_configfilename = 'txt'
        if argv[-1] in ['txt', 'hocr','pdf']:
            tesseract_configfilename = argv[-1]
    
        output_filename = argv[2] + '.' + tesseract_configfilename
    
        lang = 'eng'
        if '-l' in argv:
            lang = argv[argv.index('-l') + 1]
            if verbose:
                print("Using Tesseract OCR language parameter: {}".format(lang))
        
        #
        # calc filename in cache dir by file content and options (hash), not filename
        # so cache will be used, too for temprorary filenames and if multiple files of the same image
        #
        
        # hash of file content
        hash_filecontent = hashlib.sha256(open(input_filename, 'rb').read()).hexdigest()

        # hash of options (without the changing (temp) file names)
        options = lang

        if len(argv)>3:
            options = ' '.join(argv[3:])
            
        hash_options = hashlib.md5(options.encode('utf8')).hexdigest()
        
        cache_filename = cache_dir + lang + '-' + hash_filecontent + '-' + hash_options + '.' + tesseract_configfilename
        
        if os.path.isfile(cache_filename):
            if verbose:
                print("Copying OCR result for content of {} from cache {}".format(input_filename, cache_filename))
            # copy cached result to output filename
            shutil.copy(cache_filename, output_filename)
            return 0
    
        else:

            if verbose:
                print("OCR result not in cache, running Tesseract OCR by arguments {}".format(argv))
            
            # run tesseract and copy output file to cache
            result_code = subprocess.call(argv)

            if verbose:
                print("Copying OCR result {} to cache {}".format(output_filename, cache_filename))

            shutil.copy(output_filename, cache_filename)
        
            return result_code


#
# If started by command line (not imported for functions) get command line parameters and start OCR
#

if __name__ == "__main__":

    # read command line parameters
    argv = sys.argv
    # since runned on command line instead beeing used as Python library
    # the option argv[0] is not tesseract command but this wrapper
    # so change in new argv for OCR the command parameter to real tesseract
    argv[0] = 'tesseract'
    
    # copy OCR result from cache or run OCR by Tesseract
    result_code = tesseract_ocr(argv)
    
    sys.exit(result_code)
