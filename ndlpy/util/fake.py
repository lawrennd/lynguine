# Fake data ideas initially from https://stackoverflow.com/questions/45574191/using-python-faker-generate-different-data-for-5000-rows
import mimesis as mi
import pandas as pd

from pylatexenc.latexencode import unicode_to_latex

from mimesis import Person
from mimesis.locales import Locale
from mimesis.keys import romanize

from anyascii import anyascii

person = mi.Person("en")
addess = mi.Address()
datetime = mi.Datetime()
text = mi.Text("en")
code = mi.Code()
random = mi.random.Random()

suffices = [
    "Jr.",
    "Sr.",
    "Jr",
    "Sr",
    "Jnr",
    "Snr",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
    "IX",
    "X",
]
prefices = [
    "aan",
    "aan 't",
    "aan de",
    "aan den",
    "aan der",
    "aan het",
    "aen 't",
    "aen de",
    "af",
    "al",
    "am",
    "an",
    "an de",
    "an den",
    "an die",
    "an t",
    "auf",
    "bij",
    "bij de",
    "bij den",
    "bin",
    "chez",
    "d'",
    "da",
    "dal",
    "dalla",
    "dallo",
    "das",
    "de",
    "De",
    "de la",
    "de las",
    "de los",
    "degli",
    "dei",
    "del",
    "della",
    "delle",
    "dello",
    "den",
    "der",
    "des",
    "di",
    "do",
    "dos",
    "du",
    "Du",
    "el",
    "fitz",
    "ibn",
    "im",
    "in",
    "in 't",
    "in de",
    "in den",
    "in der",
    "in het",
    "int",
    "la",
    "le",
    "lo",
    "los",
    "mac",
    "mc",
    "O'",
    "of",
    "onder",
    "onder 't",
    "onder de",
    "onder den",
    "onder der",
    "onder het",
    "op",
    "op 't",
    "op de",
    "op den",
    "op der",
    "op het",
    "op ten",
    "over",
    "saint",
    "san",
    "sous",
    "St",
    "sur",
    "sur le",
    "t",
    "T'",
    "te",
    "ten",
    "ter",
    "then",
    "tho",
    "thoe",
    "to",
    "toe",
    "uit",
    "uit de",
    "uit den",
    "uit het",
    "uit te",
    "un",
    "une",
    "up",
    "van",
    "van 't",
    "van de",
    "van den",
    "van der",
    "van het",
    "vanden",
    "Ver",
    "vom",
    "von",
    "von dem",
    "von den",
    "von der",
    "voor",
    "y",
    "z",
    "zu",
    "zum",
    "zur",
]


def prefix(name):
    """
    Checks if name contains a prefix. If so, returns the prefix and the name without the prefix. Otherwise returns None and the name.

    :return: A tuple containing the prefix and the name without the prefix.
    :rtype: tuple
    """
    # Check through list of prefixes

    for pre in prefices[::-1]:
        if name.startswith(pre + " "):
            return pre, name[len(pre) + 1 :]
    return None, name


def suffix(name):
    """
    Returns a random suffix.

    :return: A random suffix.
    :rtype: str
    """
    # Check through list of suffices
    for suf in suffices:
        if name.endswith(" " + suf):
            return suf, name[: -len(suf) - 1]
    return None, name


def author_editor():
    """
    Returns a random author or editor name.

    :return: A random author or editor..
    :rtype: str
    """
    # First select a random locale
    # List of locales from mimesis
    locale = random.choice_enum_item(Locale)
    # Then create a person object for that locale
    with person.override_locale(locale):
        count = 0
        while True:
            count += 1
            givenName = person.first_name()
            # To fix bad data in mimesis
            if givenName[:6] == "Eugen\t":
                givenName = "Eugen"
            elif givenName == "Axel / Axl":
                givenName = "Axel"
            familyName = person.surname().replace("’", "'")
            familyName = familyName.replace("`", "")
            num_middle_names = random.randint(0, 2)
            for i in range(num_middle_names):
                middleName = person.first_name()
                # To fix bad data in mimesis
                if middleName[:6] == "Eugen\t":
                    middleName = "Eugen"
                elif middleName == "Axel / Axl":
                    middleName = "Axel"
                givenName += " " + middleName

            if locale == Locale.ZH:
                familyName = anyascii(familyName).title()
                givenName = anyascii(givenName).title()
            # Romanise Russian, Ukranian and Kazakh locales
            elif locale in (Locale.RU, Locale.UK, Locale.KK):
                roman = romanize(locale)
                familyName = roman(familyName).title()
                givenName = roman(givenName).title()
            # Romanise Greek, Farsi locales
            elif locale in (Locale.EL, Locale.FA):
                familyName = anyascii(familyName).title()
                givenName = anyascii(givenName).title()
            # Romanise Japanese locale
            elif locale == Locale.JA:
                familyName = anyascii(familyName).title()
                givenName = anyascii(givenName).title()
            # Romanise Korean locale
            elif locale == Locale.KO:
                familyName = anyascii(familyName).title()
                givenName = anyascii(givenName).title()
            if familyName is not None and givenName is not None:
                break
            if count > 100:
                raise Exception(f"Unable to generate name from locale {locale}.")

        initials = random.randint(0, 100) > 30
        if initials:
            givenNames = givenName.split()
            assert isinstance(givenNames, list)
            # Remove any empty strings
            givenNames = [name for name in givenNames if name != ""]
            # Randomly choose a from the list of given names to not initial.
            select = random.randint(0, len(givenNames) - 1)
            for i, name in enumerate(givenNames):
                if i != select:
                    givenNames[i] = name[0] + "."

            givenName = " ".join(givenNames)

        # Check for prefices and suffices
        pre, familyName = prefix(familyName)
        suf, familyName = suffix(familyName)
        author = {
            "family": familyName,
            "given": givenName,
        }
        if pre is not None:
            author["prefix"] = pre
        if suf is not None:
            author["suffix"] = suf

    return author


def row():
    familyName = person.surname()
    givenName = person.name(gender=mi.enums.Gender.FEMALE)
    date_time = datetime.datetime()
    name = familyName + "_" + givenName
    for repl in ["'", " "]:
        name = name.replace(repl, "-")
    output = {
        "name": name,
        "givenName": givenName,
        "familyName": familyName,
        "address": addess.address(),
        "email": person.email(),
        "city": addess.city(),
        "state": addess.state(),
        # "date_time": date_time,
        "tagline": text.text(quantity=3),
        "randomdata": random.randint(1000, 2000),
        "content": text.text(quantity=30),
    }
    return output


def entry_update(entry, **kwargs):
    """
    Update an entry with additional fields.

    :param entry: The entry to be updated.
    :type entry: dict
    :param kwargs: The additional fields to be added.
    :type kwargs: dict
    :return: The updated entry.
    :rtype: dict
    """
    for key, value in kwargs.items():
        entry[key] = value
    return entry


def random_entry_type():
    """
    Returns a random entry type.

    :return: A random entry type.
    :rtype: str
    """
    return random.choice(
        [
            "article",
            "book",
            "booklet",
            "conference",
            "inbook",
            "incollection",
            "inproceedings",
            "manual",
            "mastersthesis",
            "misc",
            "phdthesis",
            "proceedings",
            "techreport",
            "unpublished",
        ]
    )


def bibliography_entry():
    """
    Returns a random bibliograhy entry.

    :return: A random bibliograhy entry.
    :rtype: dict
    """

    # Create a random number of authors.
    # 95% of the time there will be only a few authors
    if random.randint(1, 100) > 5:
        num_authors = random.randint(1, 9)
    else:
        num_authors = random.randint(10, 100)

    entry_type = random_entry_type()
    # Create a random number of editors.
    if entry_type in ["book", "incollection", "inproceedings", "proceedings"]:
        # 95% of the time there will be only a few editors
        if random.randint(1, 100) > 95:
            num_editors = random.randint(1, 9)
        else:
            num_editors = random.randint(10, 100)
    else:
        num_editors = 0

    person = Person()
    # Create the authors
    authors = []
    for i in range(num_authors):
        authors.append(author_editor())

    # Create the title
    title = text.title().title()
    if title[-1] == ".":
        title = title[:-1]
    year = random.randint(1972, 2020)
    booktitle = text.title().title()

    # Create a journal title
    journal_prefix = random.choice(
        ["Journal of", "Proceedings of", "Transactions of", "Annals of", "Journal for"]
    )
    journal_suffix = random.choice(
        [
            "Monthly",
            "Quarterly",
            "Letters",
            "Transactions",
            "Annals",
            "Proceedings",
            "Review",
            "Journal",
        ]
    )
    journal_words = " ".join(text.words(quantity=random.randint(1, 3))).title()
    # Create the journal
    # With 20% probability no prefix or suffix
    random_num = random.randint(1, 100)
    if random_num < 21:
        journal = journal_words
    elif random_num < 61:
        journal = journal_prefix + " " + journal_words
    else:
        journal = journal_words + " " + journal_suffix

    if len(authors) > 0:
        key = (
            authors[0]["family"].split()[0].title()
            + "-"
            + title.split()[0].lower()
            + str(year)[2:]
        )
    elif len(editors) > 0:
        key = (
            editors[0]["family"].split()[0].title()
            + "-"
            + title.split()[0].lower()
            + str(year)[2:]
        )
    else:
        key = title[0].lower() + str(year)[2:]

    # Remove invalid characters from bibtex identifier
    key = key.replace("'", "")
    entry = {
        "ENTRYTYPE": entry_type,
        "ID": key,
        "title": title,
        "author": authors,
        "year": year,
    }

    # Create the editors
    editors = []
    for i in range(num_editors):
        editors.append(author_editor())

    if len(editors) > 0:
        entry["editor"] = editors

    if entry_type in ["article", "inproceedings", "phdthesis"]:
        entry_update(
            entry,
            abstract=text.text(quantity=20),
        )
    page1 = random.randint(1, 100)
    page2 = random.randint(1, 100)
    if page1 > page2:
        page1, page2 = page2, page1

    if entry_type in ["article"]:
        entry_update(
            entry,
            journal=journal,
            volume=random.randint(1, 100),
            issue=random.randint(1, 100),
            pages=str(page1) + "--" + str(page2),
            issn=code.issn(),
            # Return a string in digital object identifier format
            doi="10."
            + str(random.randint(1000, 9999))
            + "/"
            + str(random.randint(100000, 999999)),
        )

    if entry_type in ["incollection", "inproceedings"]:
        entry_update(
            entry,
            volume=random.randint(1, 100),
            pages=str(page1) + "--" + str(page2),
            # Return a string in digital object identifier format
            doi="10."
            + str(random.randint(1000, 9999))
            + "/"
            + str(random.randint(100000, 999999)),
        )

    if booktitle[-1] == ".":
        booktitle = booktitle[:-1]
    if entry_type in [
        "book",
        "collection",
        "proceedings",
        "incollection",
        "inproceedings",
    ]:
        entry_update(
            entry,
            booktitle=booktitle,
            publisher=" ".join(text.words(quantity=3)).title(),
            address=addess.city() + ", " + addess.country(),
            isbn=code.isbn(),
        )

    if entry_type in ["misc"]:
        entry_update(
            entry,
            howpublished=" ".join(text.words(quantity=3)).capitalize(),
        )

    if entry_type in [
        "article",
        "book",
        "booklet",
        "collection",
        "conference",
        "inbook",
        "incollection",
        "inproceedings",
        "manual",
        "mastersthesis",
        "misc",
        "phdthesis",
        "proceedings",
        "techreport",
        "unpublished",
    ]:
        entry_update(
            entry,
            volume=random.randint(1, 100),
            issue=random.randint(1, 100),
            month=random.randint(1, 12),
            note=text.text(quantity=1),
        )
    return entry


def rows(num_rows, row_type=row):
    """
    Returns a list of random rows.

    :param num_rows: The number of rows to be returned.
    :type num_rows: int
    :param row_type: The type of row to be returned.
    :type row_type: function
    :return: A list of random rows.
    :rtype: list
    """
    return [row_type() for x in range(num_rows)]


def to_bibtex_author(entry, translate_unicode=True, author_type="author"):
    """
    Convert a citeproc author/editor bibliography entry to bibtex format.

    Citeproc separates authors into family, given, prefix. Bibtext combines them into a single author field. This function converts the citeproc format to the bibtex format using liquid syntax.

    :param entry: The entry to be converted.
    :type entry: dict
    :return: The converted entry.
    :rtype: str
    """

    # Convert the authors to a single string
    authors = ""
    first = True
    for author in entry[author_type]:
        if not first:
            authors += " and "
        lastname = ""
        if "prefix" in author:
            lastname += author["prefix"] + " "
        lastname += author["family"]
        if "suffix" in author:
            lastname += " " + author["suffix"]

        # Randomly choose whether to use the comma format or not.
        if random.randint(1, 100) > 50:
            authors += lastname + ", " + author["given"]
        else:
            authors += author["given"] + " " + lastname
        first = False
    # Remove loose unicode from authors
    for key, value in {
        "\u200E": "",
        "\u00B8": "",
    }.items():
        authors = authors.replace(key, value)

    if translate_unicode:
        # Translate unicode characters to latex
        for key, value in {
            "\u0218": r"\c{S}",
            "\u0219": r"\c{s}",
            "\u021A": r"\c{T}",
            "\u021B": r"\c{t}",
        }.items():
            authors = authors.replace(key, value)
        authors = unicode_to_latex(authors)
    return authors


def to_bibtex(entry, translate_unicode=True):
    """
    Convert a citeproc bibliography entry to bibtex format.

    :param entry: The entry to be converted.
    :type entry: dict
    :return: The converted entry as a dictionary.
    :rtype: dict
    """

    converted = entry.copy()
    if "author" in converted:
        converted["author"] = to_bibtex_author(
            converted, translate_unicode=translate_unicode
        )
    if "editor" in converted:
        converted["editor"] = to_bibtex_author(
            converted, translate_unicode=translate_unicode, author_type="editor"
        )
    if translate_unicode:
        for key in [
            "title",
            "abstract",
            "journal",
            "publisher",
            "address",
            "howpublished",
            "note",
        ]:
            if key in converted:
                converted[key] = unicode_to_latex(converted[key])

    # Convert each entry to a string for bibtexparser
    for key in converted:
        converted[key] = str(converted[key])

    return converted


def row_allocation_additional_scores_series(num_ruows):
    given_name = person.first_name()
    family_name = person.surname()
    date1 = datetime.datetime()
    date2 = datetime.datetime()
    if date1 > date2:
        updated = date1
        timestamp = date2
    else:
        updated = date2
        timestamp = date1
    allocation = {
        "family": family_name,
        "given": given_name,
        "timestamp": timestamp,
        "updated": updated,
    }
    allocation["index"] = allocation["family"] + "_" + allocation["given"]
    additional = {
        "index": allocation["index"],
        "address": addess.address(),
        "email": person.email(),
        "city": addess.city(),
        "state": addess.state(),
    }
    scores = {
        "index": allocation["index"],
        "tagline": text.text(quantity=3),
        "randomdata": random.randint(1000, 2000),
        "content": text.text(quantity=30),
    }

    series = {
        "index": allocation["index"],
        "tagline": text.text(quantity=3),
        "randomdata": random.randint(1000, 2000),
        "content": text.text(quantity=30),
    }


def DataFrame(num_rows):
    return pd.DataFrame(rows(num_rows))

class Generate:
    person = mi.Person("en")
    @classmethod
    def givenName(cls):
        return person.first_name()
    @classmethod
    def familyName(cls):
        return person.surname()
    @classmethod
    def prefix(cls):
        return random.choice(prefices)
    @classmethod
    def suffix(cls):
        return random.choice(suffices)
    @classmethod
    def name(cls):
        return person.name()
    @classmethod
    def city(cls):
        return addess.city()
    @classmethod
    def state(cls):
        return addess.state()
    @classmethod
    def address(cls):
        return addess.address()
    @classmethod
    def email(cls):
        return person.email()
    @classmethod
    def date(cls):
        return datetime.datetime()
