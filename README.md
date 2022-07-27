LibreOffice-GreynirCorrect: Spelling & grammar correction for Icelandic
=======================================================================

This LibreOffice extension enables spelling and grammar correction for the Icelandic language by utilizing [GreynirCorrect](https://github.com/mideind/GreynirCorrect).

Instructions
------------

* Disable [hunspell-is](https://github.com/nifgraup/hunspell-is), go to `Tools->Options...->Language Settings->Writing Aids->Available language modules->Edit...->Language-Icelandic->Spelling` and uncheck "Hunspell SpellChecker".
* Download https://github.com/nifgraup/LibreOffice-GreynirCorrect/archive/refs/heads/master.zip
* Rename downloaded `LibreOffice-GreynirCorrect-master.zip` to `LibreOffice-GreynirCorrect.oxt`.
* Open `LibreOffice-GreynirCorrect.oxt` in LibreOffice, go to `Tools->Extension Manager...->Add`.
* The extension will complain about a missing python package `reynir_correct`, follow the instructions to install the package.

Tested with `reynir_correct` 3.4.4 and LibreOffice 7.0.4.2.
