''' Class facilitates defining regex patterns and matches
    - p = Pattern(needle)... defines a pattern to use
    - p.search(haystack) ... use like: if p.search(): match1 = p.group(1)
    - p.match(haystack)..... Like search except match
    - p.sub(new, old) ...... Not well implemented yet
'''

import re

class Pattern():
    def __init__(self, str):
        self.compile = re.compile(str)
    def search(self, haystack):
        self.result = self.compile.search(haystack)
        return self.result
    def __call__(self, haystack):
        return self.search(haystack)
    def match(self, haystack):
        self.result = self.compile.match(haystack)
        return self.result
    def group(self, val):
        return self.result.group(val)
    def sub(self, new_str, old_str):
        return self.compile.sub(new_str, old_str,1)

class Hide():

    def __init__(self, lines):

        self.hideSplunkBar = Pattern(r'(?!hideSplunkBar\s*=\s*")(true|false)(?=")')
        self.openSearch    = Pattern(r'(?!<option name="link.openSearch.visible">)(true|false)(?=</option>)')
        self.openPivot     = Pattern(r'(?!<option name="link.openPivot.visible">)(true|false)(?=</option>)')
        self.inspectSearch = Pattern(r'(?!<option name="link.inspectSearch.visible">)(true|false)(?=</option>)')

        self.lines = lines

    def change(self, type):
        self.type = type
        for i, line in enumerate(self.lines):
            print i,':',line,
            if self.hideSplunkBar(line):
                self.lines[i] = self.hideSplunkBar.sub(type, line)
            elif self.openSearch(line):
                self.lines[i] = self.openSearch.sub(type, line),
            elif self.openPivot(line):
                self.lines[i] = self.openPivot.sub(type, line),
            elif self.inspectSearch(line):
                self.lines[i] = self.inspectSearch.sub(type, line),

    def prt(self):
        prt(self.lines)
