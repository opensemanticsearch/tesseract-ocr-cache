# Tesseract OCR Cache

Tesseract OCR wrapper caching the OCR results, so Apache Tika-Server has not to reprocess slow and expensive OCR on same images again.

F.e. same images (logos or corporate identity elements), which appear in many PDF or Word documents.

Or for reindexing or new analysis of your documents because of changed ETL settings or new analysis features.

Therefore there is a tesseract wrapper which is called with same parameters like the original Tesseract command line interface (CLI):


# tesseract_cache

The commandline tool <code>[tesseract_cache](tesseract_cache)/tesseract</code> calls Tesseract OCR and caches the results to a file directory before returning the resulting text.

If you OCR the same image again, it doesn't call Tesseract OCR again but returns the result text from the cache.


# tesseract_fake

The commandline tool <code>[tesseract_fake](tesseract_fake)/tesseract</code> does not forward the call to Tesseract OCR.

It returns OCR results only if yet cached by former runs of <code>tesseract_cache/tesseract</code>.

If the image was not processed by OCR yet it will return only the string <code>[Image (no OCR yet)]</code>.

Since OCR needs most resources for often a few additional information, this approach is used to index most document contents without expensive OCR processing to be able to search for most content much earlier.

By the OCR fake text or temporary status we get the info, if Apache Tika found some images in the document, so such documents are added to another task queue for expensive OCR with lower priority than the standard text extraction tasks.


# Setup

Just set Apache Tika to use the command tesseract in directory tesseract_cache instead of the original tesseract binary directory.
