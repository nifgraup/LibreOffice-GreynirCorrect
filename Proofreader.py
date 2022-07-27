from com.sun.star.awt.MessageBoxButtons import BUTTONS_OK
from com.sun.star.awt.MessageBoxType import ERRORBOX
from com.sun.star.beans import PropertyValue
from com.sun.star.lang import Locale
from com.sun.star.lang import XServiceInfo, XServiceName, XServiceDisplayName
from com.sun.star.linguistic2 import XProofreader, XSupportedLocales
from com.sun.star.text.TextMarkupType import PROOFREADING
from textwrap import wrap
import sys
import uno
import unohelper
try:
    from reynir_correct import check_with_stats
except ImportError:
    def check_with_stats(text):
        return {"paragraphs": []}

    message = """reynir_correct not found, fix with:

{0} -m pip install -U reynir_correct""".format(sys.executable)
    try:
        import pip
    except ImportError:
        message = """Download https://bootstrap.pypa.io/get-pip.py and run:

{0} get-pip.py""".format(sys.executable) + "\n\n" + message
    ctx = uno.getComponentContext()
    sManager = ctx.ServiceManager
    toolkit = sManager.createInstance("com.sun.star.awt.Toolkit")
    msgbox = toolkit.createMessageBox(None, ERRORBOX, BUTTONS_OK, "Error initializing LibreOffice-GreynirCorrect", message)
    msgbox.execute()


ImplName = "libreoffice-greynircorrect"
SupportedServiceNames = ("com.sun.star.linguistic2.Proofreader",)


def check_grammar(text):
    errors = []
    offset = 0
    result = check_with_stats(text)
    for pg in result["paragraphs"]:
        for sent in pg:
            token_idx = []
            for t in sent.tokens:
                token_idx.append(offset)
                offset += len(t.original)

            for a in sent.annotations:
                aErr = uno.createUnoStruct("com.sun.star.linguistic2.SingleProofreadingError")
                aErr.nErrorType = PROOFREADING
                aErr.aRuleIdentifier = a.code
                aErr.aSuggestions = tuple([a.suggest]) if a.suggest else ()
                aErr.aShortComment = a.text
                if a.detail:
                    aErr.aFullComment = aErr.aShortComment + "\n\n" + "\n".join(wrap(a.detail, width=80))
                else:
                    aErr.aFullComment = aErr.aShortComment
                aErr.nErrorStart = token_idx[a.start]
                while text[aErr.nErrorStart] == " " and (aErr.nErrorStart + 1) < len(text):
                    aErr.nErrorStart = aErr.nErrorStart + 1
                if (a.end + 1) < len(token_idx):
                    end_idx = token_idx[a.end + 1]
                else:
                    end_idx = len(text)
                    while end_idx > 0 and text[end_idx - 1] == " ":
                        end_idx = end_idx - 1
                aErr.nErrorLength = end_idx - aErr.nErrorStart
                # TODO
                # p = PropertyValue()
                # p.Name = "FullCommentURL"
                # p.Value = "https://ritreglur.arnastofnun.is/#{0}".format(a.references)
                # aErr.aProperties = (p,)
                aErr.aProperties = ()

                errors.append(aErr)
    return tuple(errors)


class Impl(unohelper.Base, XProofreader, XServiceInfo, XServiceDisplayName, XServiceName, XSupportedLocales):
    def __init__(self, ctx, *args):
        self.locales = tuple([Locale('is', 'IS', '')])
        self.ignore_rules = set()

    # XServiceDisplayName
    def getServiceDisplayName(self, aLocale):
        return "GreynirCorrect: A spelling and grammar corrector for Icelandic"

    # XServiceName
    def getServiceName(self):
        # TODO: Should this be ServiceName?
        return ImplName

    # XServiceInfo
    def getImplementationName(self):
        return ImplName

    # XServiceInfo
    def supportsService(self, ServiceName):
        return (ServiceName in SupportedServiceNames)

    # XServiceInfo
    def getSupportedServiceNames(self):
        return SupportedServiceNames

    # XSupportedLocales
    def hasLocale(self, aLocale):
        return aLocale.Language == "is"

    # XSupportedLocales
    def getLocales(self):
        return self.locales

    # XProofreader
    def isSpellChecker(self):
        return True

    # XProofreader
    def doProofreading(self, nDocId, rText, rLocale, nStartOfSentencePos, nSuggestedSentenceEndPos, rProperties):
        aRes = uno.createUnoStruct("com.sun.star.linguistic2.ProofreadingResult")
        aRes.aDocumentIdentifier = nDocId
        aRes.aText = rText
        aRes.aLocale = rLocale
        aRes.nStartOfSentencePosition = nStartOfSentencePos
        aRes.nStartOfNextSentencePosition = nSuggestedSentenceEndPos
        aRes.aProperties = ()  # TODO: should this be rProperties ?
        aRes.xProofreader = self

        # PATCH FOR LO 4
        # Fix for http://nabble.documentfoundation.org/Grammar-checker-Undocumented-change-in-the-API-for-LO-4-td4030639.html
        if nStartOfSentencePos != 0:
            return aRes
        aRes.nStartOfNextSentencePosition = len(rText)
        # END OF PATCH

        l = rText[aRes.nStartOfNextSentencePosition:aRes.nStartOfNextSentencePosition+1]
        while l == " ":
            aRes.nStartOfNextSentencePosition = aRes.nStartOfNextSentencePosition + 1
            l = rText[aRes.nStartOfNextSentencePosition:aRes.nStartOfNextSentencePosition+1]
        if aRes.nStartOfNextSentencePosition == nSuggestedSentenceEndPos and l!="":
            aRes.nStartOfNextSentencePosition = nSuggestedSentenceEndPos + 1
        aRes.nBehindEndOfSentencePosition = aRes.nStartOfNextSentencePosition

        aRes.aErrors = check_grammar(rText)

        return aRes

    # XProofreader
    def ignoreRule(self, rid, aLocale):
        self.ignore_rules.add(rid)

    # XProofreader
    def resetIgnoreRules(self):
        self.ignore_rules.clear()


g_ImplementationHelper = unohelper.ImplementationHelper()
g_ImplementationHelper.addImplementation(Impl, ImplName, SupportedServiceNames)
