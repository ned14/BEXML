@echo off
cmd /c f:\python27\Scripts\pylint -E -f msvs libBEXML
cmd /c f:\python27\Scripts\pylint -E -f msvs tests
