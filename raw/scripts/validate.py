#!/usr/bin/env python3
#
# validate uralex
#
from pybtex import database
import csv
import re

DATA_FILE = "../Data.tsv"
LANGUAGES_FILE = "../Languages.tsv"
LANGUAGE_COMPILERS_FILE = "../Language_compilers.tsv"
MEANINGS_FILE = "../Meanings.tsv"
MEANING_EXAMPLES_FILE = "../Meaning_examples.tsv"
MEANING_LIST_FILE = "../Meaning_lists.tsv"
MEANING_LIST_DESC_FILE = "../Meaning_list_descriptions.tsv"
REFS_FILE = "../Citations.bib"

class UraLexValidator:
    LANG_ID = "uralex_lang"
    MNG_ID = "uralex_mng"
    GLOTTOCODE_ID = "glottocode"
    ISOCODE_ID = "iso-639-3"
    MNG_EXAMPLE_ID = "example"
    LJ_RANK_ID = "LJ_rank"
    MNG_LIST_DESC_ID = "list"
    ITEM_ID = "item"
    COGN_ID = "cogn_set"
    FORM_ID = "form_set"
    REFS = ["ref_cogn", "ref_borr", "ref_item"]
    _languages = None
    _data = None
    _meanings = None
    _language_compilers = None
    _mng_examples = None
    _mng_lists = None
    _mng_list_desc = None
    _citations = None
    def __init__(self):
        self._languages = read_table(LANGUAGES_FILE)
        self._data = read_table(DATA_FILE)
        self._language_compilers = read_table(LANGUAGE_COMPILERS_FILE)
        self._meanings = read_table(MEANINGS_FILE)
        self._mng_examples = read_table(MEANING_EXAMPLES_FILE)
        self._mng_lists = read_table(MEANING_LIST_FILE)
        self._mng_list_desc = read_table(MEANING_LIST_DESC_FILE)
        self._citations = database.parse_file(REFS_FILE)

    def __del__(self):
        pass
    
    def checkLangCodes(self):
        '''Check language codes across all files'''
        self._validateLangCodes()
        self._checkLanguagesData()
        self._checkLanguageCompilers()
        self._checkGlottoCodes()
        self._checkISOCodes()
        self._checkLanguageNames()

    def checkMeanings(self):
        self._validateMeaningCodes()
        self._checkMeaningsData()
        self._checkMeaningCoverage()
        self._checkMeaningExamples()

    def _checkMeaningCoverage(self):
        mngs = self._getMeaningCodes()
        langs = self._getLangCodes()
        coverage = {}
        for i,r in enumerate(self._data):
            try:
                coverage[r[self.MNG_ID]].append(r[self.LANG_ID])
            except KeyError:
                coverage[r[self.MNG_ID]] = [r[self.LANG_ID]]
        reference = None
        for k in coverage.keys():
            if reference is None:
                reference = coverage[k]
                continue
            if len(set(reference)) < len(set(coverage[k])):
                reference = coverage[k]
        for k in coverage.keys():
            if sorted(list(set(coverage[k]))) != sorted(list(set(reference))):
                missing_langs = set(reference)-set(coverage[k])
                missing_string = ""
                for x in missing_langs:
                    missing_string += ", " + x
                missing_string = missing_string[2:]
                print("Error (Data.tsv): Meaning %s missing for %s" % (k,missing_string))

    def _checkMeaningListMngs(self):
        mng_codes = self._getMeaningCodes()
        mlist_mng_codes = []
        for r in self._mng_lists:
            mlist_mng_codes.append(r[self.MNG_ID])
        if sorted(mlist_mng_codes) != sorted(mng_codes):
            print("Error (Meaning_lists.tsv): Meanings defined in file do not match those in Meanings.tsv")
            exit(1)
                
    def checkMeaningLists(self):
        mng_lists = []
        for i in self._mng_lists[0].keys():
            if i not in [self.MNG_ID, self.LJ_RANK_ID]:
                mng_lists.append(i)
        mng_list_desc = []
        for i,r in enumerate(self._mng_list_desc):
            mng_list_desc.append(r[self.MNG_LIST_DESC_ID])
        if sorted(mng_lists) != sorted(mng_list_desc):
            print(sorted(mng_lists),"vs.",sorted(mng_list_desc))
            print("Error (Meaning_lists.tsv): Ensure that meaning lists in this file and Meaning_list_descriptions.tsv match.")
            exit(1)
        for i,r in enumerate(self._mng_lists):
            for mlist in mng_lists:
                if r[mlist] not in ["0","1"]:
                    print("Error (Meaning_lists.tsv): meaning list %s, meaning %s: invalid character." % (mlist,r[self.MNG_ID]))
                    exit(1)
            if re.match("([0-9]+|-)" , r[self.LJ_RANK_ID]) is None:
                print("Error (Meaning_lists.tsv): Invalid Leipzig-Jakarta rank for meaning %s." % r[self.MNG_ID])
                exit(1)
        self._checkMeaningListMngs()
    
    def _getMeaningCodes(self):
        mng_codes = []        
        for i,r in enumerate(self._meanings):
            mng_codes.append(r[self.MNG_ID])
        return mng_codes
        
    def _validateMeaningCodes(self):
        mng_codes = self._getMeaningCodes()
        if len(set(mng_codes)) != len(mng_codes):
            print("Error (Meanings.tsv): Some meanings are defined multiple times.")
            exit(1)

    def _checkMeaningExamples(self):
        mng_codes = self._getMeaningCodes()
        examples = []
        for i,r in enumerate(self._mng_examples):
            examples.append(r[self.MNG_ID])
            if r[self.MNG_ID] not in mng_codes:
                print("Error (Meaning_examples.tsv): meaning %s not defined in Meanings.tsv")
                exit(1)
        for i in mng_codes:
            if i not in examples:
                print("Warning (Meaning_examples.tsv): No examples for meaning %s" % i)
        
    def _checkMeaningsData(self):
        data_meanings = []
        for i,r in enumerate(self._data):
            data_meanings.append(r[self.MNG_ID])
        mng_codes = self._getMeaningCodes()
        if sorted(list(set(data_meanings))) != sorted(list(set(mng_codes))):
            for item in data_meanings:
                if item not in mng_codes:
                    print("Error (Meanings.tsv): Used meaning %s not defined" % item)
                    exit(1)
            for item in mng_codes:
                if item not in data_meanings:
                    print("Warning (Meanings.tsv): Unused meaning %s defined" % item)

        
    def _checkGlottoCodes(self):
        for i,r in enumerate(self._languages):
            if r[self.GLOTTOCODE_ID].strip() == "":
                print("Warning (Languages.tsv): Language %s missing glottocode" % r[self.LANG_ID])

    def _checkLanguageNames(self):
        for i,r in enumerate(self._languages):
            if r["language"].strip() == "":
                print("Warning (Languages.tsv): Language %s missing unabbreviated language name (=language field)" % r[self.LANG_ID])
                
    def _checkISOCodes(self):
        for i,r in enumerate(self._languages):
            if r[self.ISOCODE_ID].strip() == "":
                print("Warning (Languages.tsv): Language %s missing ISO-639-3 code" % r[self.LANG_ID])
                
    def _getLangCodes(self):
        lang_codes = []        
        for i,r in enumerate(self._languages):
            lang_codes.append(r[self.LANG_ID])
        return lang_codes
    
    def _validateLangCodes(self):
        lang_codes = self._getLangCodes()
        if len(set(lang_codes)) != len(lang_codes):
            print("Error (Languages.tsv): Some languages are defined multiple times.")
            exit(1)

    def _getDataLangCodes(self):
        data_lang_codes = []
        for i,r in enumerate(self._data):
            data_lang_codes.append(r[self.LANG_ID])
        return data_lang_codes  

    def _checkLanguagesData(self):
        lang_codes = self._getLangCodes()
        data_lang_codes = self._getDataLangCodes()
        data_lang_codes = sorted(list(set(data_lang_codes)))
        if len(data_lang_codes) != len(lang_codes):
            for item in data_lang_codes:
                if item not in lang_codes:
                    print("Error (Languages.tsv): Used Language %s not defined" % item)
                    exit(1)
            for item in lang_codes:
                if item not in data_lang_codes:
                    print("Warning (Languages.tsv): Unused language %s defined" % item)
                    
    def _checkLanguageCompilers(self):
        compiler_codes = []
        lang_codes = self._getLangCodes()
        data_lang_codes = self._getDataLangCodes()
        for i,r in enumerate(self._language_compilers):
            compiler_codes.append(r[self.LANG_ID])
            if r[self.LANG_ID] not in lang_codes:
                print("Error (Language_compilers.tsv): Language %s not defined in Languages.tsv" % r[self.LANG_ID])
                exit(1)
        for l in sorted(list(set(data_lang_codes))):
            if l not in compiler_codes:
                print("Error (Language_compilers.tsv): Language %s used in Data.tsv but not documented in Language_compilers.tsv" % l)
                exit(1)
        for l in compiler_codes:
            if l not in data_lang_codes:
                print("Warning (Language_compilers.tsv): Unused language %s defined" % l)

    def checkItems(self):
        for i,r in enumerate(self._data):
            if r[self.ITEM_ID].strip() == "":
                print("Error (Data.tsv): line %i -- language %s, item %s is empty." % (i+1, r[self.LANG_ID],r[self.MNG_ID]))
                exit(1)
            if r[self.ITEM_ID][0] == "[" and r[self.ITEM_ID][-1] == "]":
                if re.match("(Form not found|Not reconstructable|No equivalent)",r[self.ITEM_ID][1:-1]) is None:
                    print("Error (Data.tsv): line %i -- language %s, item %s: unrecognized item %s." % (i+1, r[self.LANG_ID],r[self.MNG_ID], r[self.ITEM_ID]))
                    exit(1)

    def checkCognates(self):
        for i,r in enumerate(self._data):
            if re.match("(0|[a-z]+|\?)",r[self.COGN_ID]) is None:
                print("Error (Data.tsv): line %i -- language %s, meaning %s: invalid cognate character %s for item %s." % (i+1, r[self.LANG_ID],r[self.MNG_ID],r[self.COGN_ID], r[self.ITEM_ID]))
                exit(1)
            if r[self.COGN_ID] == "0" and r[self.ITEM_ID] != "[No equivalent]": 
                print("Error (Data.tsv): line %i -- language %s, meaning %s: Cognate character '0' only valid for items marked [No equivalent]." % (i+1, r[self.LANG_ID],r[self.MNG_ID]))
                exit(1)
            if r[self.COGN_ID] == "?" and r[self.ITEM_ID] not in ["[Not reconstructable]","[Form not found]"]:
                print("Error (Data.tsv): line %i -- language %s, meaning %s: Cognate character '?' only valid for items marked [Not reconstructable] or [Form not found]." % (i+1, r[self.LANG_ID],r[self.MNG_ID]))
    def checkCorrelates(self):
        for i,r in enumerate(self._data):
            if re.match("([0-9]+|\?)",r[self.FORM_ID]) is None:
                print("Error (Data.tsv): line %i -- language %s, meaning %s: invalid correlate character %s for item %s." % (i+1, r[self.LANG_ID],r[self.MNG_ID],r[self.FORM_ID], r[self.ITEM_ID]))
                exit(1)
            if r[self.FORM_ID] == "0" and r[self.ITEM_ID] != "[No equivalent]": 
                print("Error (Data.tsv): line %i -- language %s, meaning %s: Correlate character '0' only valid for items marked [No equivalent]." % (i+1, r[self.LANG_ID],r[self.MNG_ID]))
                exit(1)
            if r[self.FORM_ID] == "?" and r[self.ITEM_ID] not in ["[Not reconstructable]","[Form not found]"]:
                print("Error (Data.tsv): line %i -- language %s, meaning %s: Correlate character '?' only valid for items marked [Not reconstructable] or [Form not found]." % (i+1, r[self.LANG_ID],r[self.MNG_ID]))
    def checkReferences(self):
        refs = []
        for i,r in enumerate(self._data):
            for ref in self.REFS:
                if r[ref] != "":
                    refs += (r[ref].split(","))
        refs_clean = []
        for i in refs:
            if i.strip() != "":
                refs_clean.append(i.strip())
        refs_clean = set(refs_clean)
        bibtex_entries = []
        #print(refs)
        for e in self._citations.entries:
            bibtex_entries.append(e)
        for i in refs_clean:
            if i not in bibtex_entries:
                print("Error (Citations.bib): Missing reference %s, which is present in Data.tsv." % i)
                exit(1)
        for i in bibtex_entries:
            if i not in refs_clean:
                print("Warning (Citations.bib: Unused reference %s present in citations file" % i)

def read_table(filename, delim = "\t"):
    output = []
    with open(filename,"r") as data:
        reader = csv.DictReader(data, delimiter = delim)
        for row in reader:
            output.append(row)
        return output


if __name__ == '__main__':
    u = UraLexValidator()
    u.checkLangCodes()
    u.checkMeanings()
    u.checkMeaningLists()
    u.checkItems()
    u.checkCognates()
    u.checkCorrelates()
    u.checkReferences()
