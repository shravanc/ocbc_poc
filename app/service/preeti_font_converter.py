unicodeatoz = ["ब", "द", "अ", "म", "भ", "ा", "न", "ज", "ष्", "व", "प", "ि", "फ", "ल", "य", "उ", "त्र", "च", "क", "त",
               "ग", "ख", "ध", "ह", "थ", "श"]
unicodeAtoZ = ["ब्", "ध", "ऋ", "म्", "भ्", "ँ", "न्", "ज्", "क्ष्", "व्", "प्", "ी", "ः", "ल्", "इ", "ए", "त्त", "च्",
               "क्", "त्", "ग्", "ख्", "ध्", "ह्", "थ्", "श्"]
unicode0to9 = ["ण्", "ज्ञ", "द्द", "घ", "द्ध", "छ", "ट", "ठ", "ड", "ढ"]

symbolsDict = {
    "~": "ञ्",
    "`": "ञ",
    "!": "१",
    "@": "२",
    "#": "३",
    "$": "४",
    "%": "५",
    "^": "६",
    "&": "७",
    "*": "८",
    "(": "९",
    ")": "०",
    "-": "(",
    "_": ")",
    "+": "ं",
    "[": "ृ",
    "{": "र्",
    "]": "े",
    "}": "ै",
    "\\": "्",
    "|": "्र",
    ";": "स",
    ":": "स्",
    "'": "ु",
    "\"": "ू",
    ",": ",",
    "<": "?",
    ".": "।",
    ">": "श्र",
    "/": "र",
    "?": "रु",
    "=": ".",
    "ˆ": "फ्",
    "Î": "ङ्ख",
    "å": "द्व",
    "÷": "/"
}


# unicodeToPreetiDict = \
#     {
#         "अ": "c",
#         "आ": "cf",
#         "ा": "f",
#         "इ": "O",
#         "ई": "O{",
#         "र्": "{",
#         "उ": "p",
#         "ए": "P",
#         "े": "]",
#         "ै": "}",
#         "ो": "f]",
#         "ौ": "f}",
#         "ओ": "cf]",
#         "औ": "cf}",
#         "ं": "+",
#         "ँ": "F",
#         "ि": "l",
#         "ी": "L",
#         "ु": "'",
#         "ू": '"',
#         "क": "s",
#         "ख": "v",
#         "ग": "u",
#         "घ": "3",
#         "ङ": "ª",
#         "च": "r",
#         "छ": "5",
#         "ज": "h",
#         "झ": "´",
#         "ञ": "`",
#         "ट": "6",
#         "ठ": "7",
#         "ड": "8",
#         "ढ": "9",
#         "ण": "0f",
#         "त": "t",
#         "थ": "y",
#         "द": "b",
#         "ध": "w",
#         "न": "g",
#         "प": "k",
#         "फ": "km",
#         "ब": "a",
#         "भ": "e",
#         "म": "d",
#         "य": "o",
#         "र": "/",
#         "रू": "?",
#         "ृ": "[",
#         "ल": "n",
#         "व": "j",
#         "स": ";",
#         "श": "z",
#         "ष": "if",
#         "ज्ञ": "1",
#         "ह": "x",
#         "१": "!",
#         "२": "@",
#         "३": "#",
#         "४": "$",
#         "५": "%",
#         "६": "^",
#         "७": "&",
#         "८": "*",
#         "९": "(",
#         "०": ")",
#         "।": ".",
#         "्": "\\",
#         "ऊ": "pm",
#         "-": " ",
#         "(": "-",
#         ")": "_"
#     }


def convert(inputfile):
    # with open(inputfile, "r") as fp:
    #     preeti = fp.read()
    converted = ''
    normalizedpreeti = normalizePreeti(inputfile)
    for index, character in enumerate(normalizedpreeti):
        try:
            if ord(character) >= 97 and ord(character) <= 122:
                converted += unicodeatoz[ord(character) - 97]
            elif ord(character) >= 65 and ord(character) <= 90:
                converted += unicodeAtoZ[ord(character) - 65]
            elif ord(character) >= 48 and ord(character) <= 57:
                converted += unicode0to9[ord(character) - 48]
            else:
                converted += symbolsDict[character]
        except KeyError:
            converted += character
    return converted


def normalizePreeti(preetitxt):
    normalized = ''
    previoussymbol = ''
    preetitxt = preetitxt.replace('qm', 's|')
    preetitxt = preetitxt.replace('f]', 'ो')
    preetitxt = preetitxt.replace('km', 'फ')
    preetitxt = preetitxt.replace('0f', 'ण')
    preetitxt = preetitxt.replace('If', 'क्ष')
    preetitxt = preetitxt.replace('if', 'ष')
    preetitxt = preetitxt.replace('cf', 'आ')
    index = -1
    while index + 1 < len(preetitxt):
        index += 1
        character = preetitxt[index]
        try:
            if preetitxt[index + 2] == '{':
                if preetitxt[index + 1] == 'f' or preetitxt[index + 1] == 'ो':
                    normalized += '{' + character + preetitxt[index + 1]
                    index += 2
                    continue
            if preetitxt[index + 1] == '{':
                if character != 'f':
                    normalized += '{' + character
                    index += 1
                    continue
        except IndexError:
            pass
        if character == 'l':
            previoussymbol = 'l'
            continue
        else:
            normalized += character + previoussymbol
            previoussymbol = ''
    return normalized

# def normalizeUnicode(unicodetext):
#     index = -1
#     normalized = ''
#     while index + 1 < len(unicodetext):
#         index += 1
#         character = unicodetext[index]
#         try:
#             try:
#                 if character != 'र':  # for aadha akshars
#                     if unicodetext[index + 1] == '्' and unicodetext[index + 2] != ' ' and unicodetext[
#                         index + 2] != '।' and unicodetext[index + 2] != ',':
#                         if unicodetext[index + 2] != 'र':
#                             if unicodeToPreetiDict[character] in list('wertyuxasdghjkzvn'):
#                                 normalized += chr(ord(unicodeToPreetiDict[character]) - 32)
#                                 index += 1
#                                 continue
#                             elif character == 'स':
#                                 normalized += ':'
#                                 index += 1
#                                 continue
#                             elif character == 'ष':
#                                 normalized += 'i'
#                                 index += 1
#                                 continue
#                 if unicodetext[index - 1] != 'र' and character == '्' and unicodetext[
#                     index + 1] == 'र':  # for खुट्टा चिर्ने चिन्ह in the likes of क्रम and ट्रक
#                     if unicodetext[index - 1] != 'ट' and unicodetext[index - 1] != 'ठ' and unicodetext[
#                         index - 1] != 'ड':
#                         normalized += '|'  # for sign as in क्रम
#                         index += 1
#                         continue
#                     else:
#                         normalized += '«'  # for sign as in ट्रक
#                         index += 1
#                         continue
#             except IndexError:
#                 pass
#             normalized += character
#         except KeyError:
#             normalized += character
#     normalized = normalized.replace('त|', 'q')  # for त्र
#     return normalized
#
#
# def convert(inputfile):
#     with open(inputfile, "r", encoding='utf-8') as fp:
#         unicodetext = fp.read()
#     normalizedunicodetext = normalizeUnicode(unicodetext)
#     converted = ''
#     index = -1
#     while index + 1 < len(normalizedunicodetext):
#         index += 1
#         character = normalizedunicodetext[index]
#         if character == '\ufeff':
#             continue
#         try:
#             try:
#                 if normalizedunicodetext[index + 1] == 'ि':  # for normal hraswo ukaar
#                     if character == 'q':
#                         converted += 'l' + character
#                     else:
#                         converted += 'l' + unicodeToPreetiDict[character]
#                     index += 1
#                     continue
#
#                 if normalizedunicodetext[index + 2] == 'ि':  # for constructs like त्ति
#                     if character in list('WERTYUXASDGHJK:ZVN'):
#                         if normalizedunicodetext[index + 1] != 'q':  # if not like न्त्रि
#                             converted += 'l' + character + unicodeToPreetiDict[normalizedunicodetext[index + 1]]
#                             index += 2
#                             continue
#                         elif normalizedunicodetext[index + 1] == 'q':
#                             converted += 'l' + character + normalizedunicodetext[index + 1]
#                             index += 2
#                             continue
#
#                 if normalizedunicodetext[index + 1] == '्' and character == 'र':  # for reph as in वार्ता
#                     if normalizedunicodetext[index + 3] == 'ा' or normalizedunicodetext[index + 3] == 'ो' or \
#                             normalizedunicodetext[index + 3] == 'ौ' or normalizedunicodetext[index + 3] == 'े' or \
#                             normalizedunicodetext[index + 3] == 'ै' or normalizedunicodetext[index + 3] == 'ी':
#                         converted += unicodeToPreetiDict[normalizedunicodetext[index + 2]] + unicodeToPreetiDict[
#                             normalizedunicodetext[index + 3]] + '{'
#                         index += 3
#                         continue
#                     elif normalizedunicodetext[index + 3] == 'ि':
#                         converted += unicodeToPreetiDict[normalizedunicodetext[index + 3]] + unicodeToPreetiDict[
#                             normalizedunicodetext[index + 2]] + '{'
#                         index += 3
#                         continue
#                     converted += unicodeToPreetiDict[normalizedunicodetext[index + 2]] + '{'
#                     index += 2
#                     continue
#
#                 if normalizedunicodetext[index + 3] == 'ि':  # for the likes of ष्ट्रिय
#                     if normalizedunicodetext[index + 2] == '|' or normalizedunicodetext[index + 2] == '«':
#                         if character in list('WERTYUXASDGHJK:ZVNIi'):
#                             converted += 'l' + character + unicodeToPreetiDict[normalizedunicodetext[index + 1]] + \
#                                          normalizedunicodetext[index + 2]
#                             index += 3
#                             continue
#
#             except IndexError:
#                 pass
#             converted += unicodeToPreetiDict[character]
#         except KeyError:
#             converted += character
#
#     converted = converted.replace('Si', 'I')  # Si in preeti is aadha ka aadha ष, so replace with I which is aadha क्ष
#     converted = converted.replace('H`', '1')  # H` is the product of composite nature of unicode ज्ञ
#     converted = converted.replace('b\w', '4')  # b\w means in preeti द halanta ध, so replace the composite
#     converted = converted.replace('z|', '>')  # composite for श्र
#     converted = converted.replace("/'", '?')  # composite for रु
#     converted = converted.replace('/"', '¿')  # composite for रू
#     converted = converted.replace('Tt', 'Q')  # composite for त्त
#     converted = converted.replace('b\lj', 'lå')  # composite for द्वि
#     converted = converted.replace('b\j', 'å')  # composite for द्व
#     converted = converted.replace('0f\\', '0')  # composite for ण् to get the aadha ण in say गण्डक
#     converted = converted.replace('`\\', '~')  # composite for aadha ञ्
#     return converted
