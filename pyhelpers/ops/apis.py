"""
API-related utilities.
"""

import datetime
import html
import os
import re
import secrets
import string

from .._cache import _add_slashes, _confirmed, _init_requests_session, _print_failure_message, \
    _USER_AGENT_STRINGS


class CrossRefOrcid:
    """
    A class to interact with the ORCID Public API and CrossRef API
    to retrieve metadata about academic publications.
    """

    #: The ORCID environment for the Public API on the production ORCID Registry.
    ORCID_PUBLIC_API_ENDPOINT: str = 'https://pub.orcid.org/v3.0'

    #: The CrossRef REST API endpoint for querying metadata about published works.
    CROSSREF_REST_API_ENDPOINT: str = 'https://api.crossref.org/works'

    #: The Zenodo REST API endpoint for access to records stored in Zenodo.
    ZENODO_REST_API_ENDPOINT: str = 'https://zenodo.org/api/records'

    #: Templates of various styles of citations.
    CITATION_STYLES: dict = {
        "APA": "{author} ({year}). {title}. {publication}, {pages}. https://doi.org/{doi}",
        "MLA": "{author} \"{title}.\" {publication}, {year}, pp. {pages}.",
        "Chicago": "{author} {year}. \"{title}.\" {publication}, {pages}. https://doi.org/{doi}",
        "Harvard": "{author} ({year}) '{title}', {publication}, pp. {pages}. "
                   "Available at: https://doi.org/{doi} [Accessed {accessed}].",
        "IEEE": "[{index}] {author}, \"{title},\" {publication}, pp. {pages}, {year}, doi:{doi}.",
        "Vancouver": "{author} {title}. {publication}. {year};{pages}. doi:{doi}.",
    }

    def __init__(self, my_name="", requests_headers=None):
        """
        :ivar my_name: My name to be bolded in the author list; defaults to ``"Fu, Qian"``.
        :vartype my_name: str
        :ivar requests_headers: HTTP headers used for making requests to external APIs;
            defaults to ``{"Accept": "application/json"}``.
        :vartype requests_headers: dict

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> co.ORCID_PUBLIC_API_ENDPOINT
            'https://pub.orcid.org/v3.0'
            >>> co.CROSSREF_REST_API_ENDPOINT
            'https://api.crossref.org/works'
            >>> list(co.CITATION_STYLES)
            ['APA', 'MLA', 'Chicago', 'Harvard', 'IEEE', 'Vancouver']
        """

        self.my_name = my_name

        self.requests_headers = requests_headers or {
            'accept': 'application/json',
            'user-agent': secrets.choice(
                _USER_AGENT_STRINGS.get(secrets.choice(list(_USER_AGENT_STRINGS)))),
        }

    def get_orcid_profile(self, orcid_id, section=None, verbose=False):
        # noinspection PyShadowingNames
        """
        Fetches the ORCID profile for a given ORCID ID.

        :param orcid_id: ORCID iD of the researcher.
        :type orcid_id: str
        :param section: Specific section of the profile (e.g. 'works'); defaults to ``None``.
        :type section: str | None
        :param verbose: Whether to print relevant information in the console; defaults to ``False``.
        :type verbose: bool | int
        :return: A dictionary containing profile data, or ``None`` if an error occurs.
        :rtype: dict | None

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> profile_data = co.get_orcid_profile(orcid_id)
            >>> list(profile_data.keys())
            ['orcid-identifier',
             'preferences',
             'history',
             'person',
             'activities-summary',
             'path']
        """

        url = f"{self.ORCID_PUBLIC_API_ENDPOINT}/{orcid_id}/{section.lower() if section else ''}"

        session = _init_requests_session(url=url)

        with session.get(url=url, stream=True, headers=self.requests_headers) as response:
            if response.status_code == 200:
                profile_data = response.json()  # ORCID profile data as a dictionary
                return profile_data
            else:
                if verbose:
                    print(f"Error: {response.status_code}. Check `response.text` for details.")

    def get_list_of_works(self, orcid_id):
        # noinspection PyShadowingNames
        """
        Fetches a list of works from an ORCID profile.

        :param orcid_id: ORCID ID of the researcher.
        :type orcid_id: str
        :return: A list of works with titles and years.
        :rtype: list[str]

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> list_of_works = co.get_list_of_works(orcid_id)
            >>> list_of_works[-1]
            'A Review on Transit Assignment Modelling Approaches to Congested Networks: A New...
        """

        profile_data = self.get_orcid_profile(orcid_id=orcid_id)

        try:
            works = profile_data["activities-summary"]["works"]["group"]
            list_of_works = []
            for work in works:
                title = work["work-summary"][0]["title"]["title"]["value"]
                year = work["work-summary"][0]. \
                    get("publication-date", {}). \
                    get("year", {}). \
                    get("value", "N/A")
                list_of_works.append(f"{title} ({year})")

            return list_of_works

        except KeyError:
            print("No works available.")

    def _get_crossref_metadata(self, doi):
        url = f"{self.CROSSREF_REST_API_ENDPOINT}/{doi}"

        session = _init_requests_session(url=url)

        with session.get(url=url, stream=True, headers=self.requests_headers) as response:
            if response.status_code == 200:
                data = response.json().get("message", {})
                metadata = {
                    "journal": data.get("container-title", [""])[0],  # Journal Name
                    "conference": data.get("event", {}).get("name", ""),  # Conference Name
                    "volume": data.get("volume", ""),
                    "issue": data.get("issue", ""),
                    "pages": data.get("page", ""),
                    "authors": ", ".join(
                        [author.get("family", "") + ", " + author.get("given", "")
                         for author in
                         data.get("author", []) if "family" in author]) or "Unknown Author",
                }
                return metadata

            return {}

    def _get_zenodo_metadata(self, doi):
        url = f"{self.ZENODO_REST_API_ENDPOINT}/{doi.split('.')[-1]}"

        session = _init_requests_session(url=url)

        with session.get(url=url, stream=True, headers=self.requests_headers) as response:
            if response.status_code == 200:
                data = response.json().get("metadata", {})
                metadata = {
                    "journal": data.get("resource_type", {}).get("title", ""),
                    "conference": data.get("meeting", {}).get("title", ""),
                    "volume": data.get("volume", ""),
                    "issue": data.get("issue", ""),
                    "pages": data.get("pages", ""),
                    "publisher": "Zenodo",
                    "authors": ", ".join(
                        [author.get("name", "")
                         for author in data.get("creators", [])]) or "Unknown Author",
                }
                return metadata

            return {}

    def get_metadata_from_doi(self, doi):
        # noinspection PyShadowingNames
        """
        Fetch full metadata from CrossRef using DOI.

        :param doi: The DOI of the publication.
        :type doi: str
        :return: A dictionary containing metadata.
        :rtype: dict

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> doi = 'https://doi.org/10.1016/j.jii.2024.100729'
            >>> co.get_metadata_from_doi(doi)
            {'journal': 'Journal of Industrial Information Integration',
             'conference': '',
             'volume': '42',
             'issue': '',
             'pages': '100729',
             'authors': 'Fu, Qian, Nicholson, Gemma L., Easton, John M.'}
        """

        return self._get_crossref_metadata(doi) or self._get_zenodo_metadata(doi) or {}

    def fetch_orcid_works(self, orcid_id, work_types=None, recent_years=2):
        # noinspection PyShadowingNames
        """
        Fetch recent works from ORCID and enrich with metadata from DOI.

        :param orcid_id: ORCID iD of the researcher.
        :type orcid_id: str
        :param work_types: Work type(s) to include
            (e.g. 'journal-article' or ['book', 'conference-paper']); defaults to ``None``.
        :type work_types: str | list | None
        :param recent_years: Number of recent years to include; defaults to ``2``.
        :type recent_years: int
        :return: A list of extracted reference dictionaries.
        :rtype: list[dict]

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> ref_data = co.fetch_orcid_works(orcid_id)  # Past two years
            >>> type(ref_data)
            list
            >>> # ref_data = co.fetch_orcid_works(orcid_id, recent_years=5)  # Past five years
            >>> # for ref_dat in ref_data:
            ... #     print(ref_dat)
        """

        data = self.get_orcid_profile(orcid_id=orcid_id, section='works')
        works = data.get("group", [])  # ORCID stores works in "group"

        ref_data = []
        current_year = datetime.datetime.now().year  # Get the current year
        recent_years_ = {
            str(current_year - x) for x in range(recent_years if recent_years else 100)}

        if work_types:
            work_types = [
                wt.lower() for wt in ([work_types] if isinstance(work_types, str) else work_types)]

        for work in works:
            summary = work.get("work-summary", [{}])[0]
            work_type = summary.get("type", "").replace("-", " ").title()  # Normalize work type

            # Skip if work type does not match the filter (when work_types is set)
            if work_types:
                if not any(wt in work_type.lower() for wt in work_types):
                    continue

            # Extract publication year
            year = summary.get("publication-date", {}).get("year", {}).get("value", "")
            if year not in recent_years_:  # Skip if not in the last two years
                continue

            # Extract details of journal papers:
            title = summary.get("title", {}).get("title", {}).get("value", "")
            doi = None

            # Extract DOI or other external IDs
            external_ids = summary.get("external-ids", {}).get("external-id", [])
            for ext_id in external_ids:
                if ext_id.get("external-id-type") == "doi":
                    doi = ext_id.get("external-id-value")
                    break

            metadata = self.get_metadata_from_doi(doi) if doi else {}

            # Build reference dictionary, excluding empty fields
            ref_dat = {
                "author": metadata.get("authors", "Unknown Author"),
                "year": year if year else None,
                "title": title if title else None,
                "work_type": work_type if work_type else "Other",
                "journal": metadata.get("journal", None),
                "conference": metadata.get("conference", None),
                "volume": metadata.get("volume", None),
                "issue": metadata.get("issue", None),
                "pages": metadata.get("pages", None),
                "publisher": metadata.get("publisher", None),
                "doi": f"https://doi.org/{doi}" if doi else None,
            }

            ref_dat = {k: v for k, v in ref_dat.items() if v}  # Remove None values
            ref_data.append(ref_dat)

        return ref_data

    def _format_author_names(self, author_str, corresponding_author=None):
        """
        Converts full author names to "Surname, F." format.

        :param author_str: A string of author names.
        :type author_str: str
        :return: Formatted author names.
        :rtype: str
        """

        authors = author_str.split(", ")  # Split by ", " to separate surname and given names
        formatted_authors = []

        for i in range(0, len(authors) - 1, 2):
            surname = authors[i]  # Last name
            given_names = authors[i + 1].split()  # First & middle names

            # Convert given names to initials, removing spaces between consecutive initials
            initials = "".join([name[0] + "." for name in given_names])

            # Format the author name
            author_name = f"{surname}, {initials}"

            # Bold your name
            if self.my_name in {author_name, f"{surname}, {' '.join(given_names)}"}:
                author_name = f"**{author_name}**"

            # Add an asterisk (*) as a superscript to the corresponding author
            if corresponding_author and author_name == corresponding_author:
                author_name = f"{author_name}<sup>*</sup>"

            formatted_authors.append(author_name)

        return ", ".join(formatted_authors)

    @staticmethod
    def _preprocess_doi(doi):
        """
        Ensures the DOI is formatted correctly with ``'https://doi.org/'``.

        :param doi: The DOI to preprocess.
        :type doi: str
        :return: Formatted DOI.
        :rtype: str
        """

        doi = doi.strip()  # Remove any surrounding whitespace
        return doi if doi.startswith("https://doi.org/") else f"https://doi.org/{doi}"

    @staticmethod
    def _clean_punctuation(text):
        """
        Cleans up extra punctuation, spaces, and unnecessary symbols left by missing placeholders.

        :param text: The text to clean.
        :type text: str
        :return: Cleaned text.
        :rtype: str
        """

        text = re.sub(r'\(\s*[,;]*\s*\)', '', text)  # Empty parentheses
        text = re.sub(r'\s*,\s*([.)])', r'\1', text)  # Commas before closing brackets or periods
        text = re.sub(r'\s*\(\s*\)', '', text)  # Empty parentheses again
        text = re.sub(r'\s*[,;]\s*$', '', text)  # Trailing commas/semicolons
        text = re.sub(r'\s+', ' ', text).strip()  # Spaces

        text = re.sub(r"Available at: \s*\[Accessed \s*]", "", text)  # Remove empty "Available at"
        text = re.sub(r"Available at: \s*[\[\]]?", "", text)  # Remove "Available at" if empty URL
        text = re.sub(r"\[Accessed \s*]", "", text)  # Remove empty "Accessed" brackets

        return text

    def _format_reference(self, ref_dat, style='APA', index=1):
        # noinspection PyShadowingNames
        """
        Formats a citation string (without missing placeholders).

        :param ref_dat: The reference data to format.
        :type ref_dat: dict
        :param style: The citation style to use; defaults to ``'APA'``.
        :type style: str
        :param index: The index for IEEE style; defaults to ``1``.
        :type index: int
        :return: Formatted citation string.
        :rtype: str

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> ref_data = co.fetch_orcid_works(orcid_id)  # Past two years
            >>> ref_dat = ref_data[0]
            >>> reference = co._format_reference(ref_dat, style="APA")
            >>> reference

        """

        if style in self.CITATION_STYLES:
            formatter = string.Formatter()
            formatted_parts = []

            # Determine the publication field based on work_type
            publication = ref_dat.get("journal", "")

            for literal_text, field_name, _, _ in formatter.parse(self.CITATION_STYLES[style]):
                if field_name is None:  # Keep literal text
                    formatted_parts.append(literal_text)

                elif field_name == "author" and field_name in ref_dat:  # Format authors
                    corresponding_author = ref_dat.get("corresponding_author", None)
                    author_names = self._format_author_names(
                        author_str=ref_dat[field_name], corresponding_author=corresponding_author)
                    formatted_parts.append(literal_text + author_names)

                elif field_name == "doi" and field_name in ref_dat:  # Ensure DOI format
                    literal_text_ = literal_text.replace('https://doi.org/', '')
                    doi = self._preprocess_doi(ref_dat[field_name])
                    if 'doi:' in literal_text:
                        doi = doi.replace('https://doi.org/', '')
                    formatted_parts.append(f"{literal_text_}{doi}")

                elif field_name == "index":  # Ensure IEEE gets an index
                    formatted_parts.append(literal_text + str(index))

                elif field_name == "publication":  # Use the determined publication field
                    formatted_parts.append(literal_text + html.unescape(publication))

                elif field_name in ref_dat and ref_dat[field_name]:  # Add field value
                    formatted_parts.append(literal_text + str(ref_dat[field_name]))

                else:
                    formatted_parts.append(literal_text)  # Remove missing placeholders

            reference = self._clean_punctuation("".join(formatted_parts))

            return reference

        else:
            print("Style not found!")

    def format_references(self, ref_data, style='APA'):
        # noinspection PyShadowingNames
        """
        Formats multiple references in a given citation style.

        :param ref_data: A collection of reference dictionaries or a single reference.
        :type ref_data: list | dict | typing.Iterable
        :param style: The citation style to use; defaults to ``'APA'``.
        :type style: str
        :return: A list of formatted citation strings.
        :rtype: list[str]

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> ref_data = co.fetch_orcid_works(orcid_id)  # Past two years
            >>> references = co.format_references(ref_data, style='APA')
            >>> references[-1]
            'Fu, Q., Easton, J.M., Burrow, M.P.N. (2024). Development of an Integrated Computing...
        """

        if isinstance(ref_data, dict):
            ref_data = [ref_data]  # Convert single dictionary to list

        references = [
            self._format_reference(ref_dat=ref_dat, style=style, index=i + 1)
            for i, ref_dat in enumerate(ref_data)]

        # # Add a footnote for the corresponding author
        # footnote = "\n\n<sup>*</sup> Corresponding author"
        # references.append(footnote)

        return references

    def fetch_references(self, orcid_id, work_types=None, recent_years=2, style='APA'):
        # noinspection PyShadowingNames
        """
        Fetches and formats references from an ORCID profile.

        :param orcid_id: ORCID iD of the researcher.
        :type orcid_id: str
        :param work_types: Work type(s) to include; defaults to ``None``.
        :type work_types: str | list | None
        :param recent_years: Number of recent years to include; defaults to ``2``.
        :type recent_years: int
        :param style: The citation style to use; defaults to ``'APA'``.
        :type style: str
        :return: A list of formatted citation strings.
        :rtype: list[str]

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> references = co.fetch_references(orcid_id)
            >>> references[-1]
            'Fu, Q., Easton, J.M., Burrow, M.P.N. (2024). Development of an Integrated Computing...
        """

        ref_data = self.fetch_orcid_works(
            orcid_id=orcid_id, work_types=work_types, recent_years=recent_years)

        if isinstance(ref_data, dict):
            ref_data = [ref_data]  # Convert single dictionary to list

        references = self.format_references(ref_data, style=style)

        return references

    @classmethod
    def _update_references(cls, references, limit=3, file_path="README.md", heading_level=3,
                           heading="Recent publications", heading_suffix=":"):
        # noinspection PyShadowingNames
        """
        Updates the "Recent publications" section in a Markdown file with a new list of citations.

        :param references: A list of reference strings to add to the
            ``"Recent publications"`` section.
        :type references: list[str]
        :param limit: The maximum number of the references to be included; defaults to ``3``.
        :type limit: int | None
        :param file_path: Path to the Markdown file; defaults to ``"README.md"``.
        :type file_path: str
        :param heading_level: The level of the heading under which the contents are to be updated;
            defaults to ``3``.
        :type heading_level: int
        :param heading: The Markdown heading for the references section;
            defaults to ``"Recent publications"``.
        :param heading_suffix: Suffix to the ``heading``; defaults to ``":"``.
        :type heading_suffix: str | None
        :type heading: str

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> references = co.fetch_references(orcid_id)
            >>> co._update_references(references, verbose=True)
            Updating "Recent publications" in README.md ... Done.
            >>> references = co.fetch_references(orcid_id, recent_years=5)
            >>> co._update_references(references, verbose=True)
            Updating "Recent publications" in README.md ... Done.
        """

        heading_ = f"{'#' * heading_level} {heading}{heading_suffix or ''}"

        with open(file_path, "r") as file:  # Read the existing content of the file
            content = file.read()

        if heading_ in content:  # Remove the existing "References" section (if it exists)
            content = content.split(heading_)[0].strip()

        # Write the updated content (excluding the old "References" section)
        with open(file_path, "w") as file:
            file.write(content)

            file.write(f"\n\n{heading_}\n\n")  # Add the new "Recent publications" section
            for reference in references[:(limit if limit else len(references))]:
                file.write(f"- {reference}\n")

    def update_references(self, orcid_id, work_types=None, recent_years=2, style='APA',
                          file_path="README.md", heading="Recent publications", heading_level=3,
                          heading_suffix=":", confirmation_required=True, verbose=False,
                          raise_error=False):
        # noinspection PyShadowingNames
        """
        Updates the "Recent publications" section in a Markdown file with a new list of citations.

        :param orcid_id: ORCID iD of the researcher.
        :type orcid_id: str
        :param work_types: Work type(s) to include; defaults to ``None``.
        :type work_types: str | list | None
        :param recent_years: Number of recent years to include; defaults to ``2``.
        :type recent_years: int
        :param style: The citation style to use; defaults to ``'APA'``.
        :type style: str
        :param file_path: Path to the Markdown file; defaults to ``"README.md"``.
        :type file_path: str
        :param heading_level: The level of the heading under which the contents are to be updated;
            defaults to ``3``.
        :type heading_level: int
        :param heading: The Markdown heading for the references section;
            defaults to ``"Recent publications"``.
        :type heading: str
        :param heading_suffix: Suffix to the ``heading``; defaults to ``":"``.
        :type heading_suffix: str | None
        :param confirmation_required: Whether to prompt for confirmation before proceeding;
            defaults to ``True``.
        :type confirmation_required: bool
        :param verbose: If ``True``, prints status messages; defaults to ``False``.
        :type verbose: bool
        :param raise_error: Whether to raise the provided exception;
            if ``raise_error=False`` (default), the error will be suppressed.
        :type raise_error: bool

        **Examples**::

            >>> from pyhelpers.ops import CrossRefOrcid
            >>> co = CrossRefOrcid()
            >>> orcid_id = '0000-0002-6502-9934'
            >>> co.update_references(orcid_id, verbose=True)
            To write/update references in README.md
            ? [No]|Yes: yes
            Updating "Recent publications" in README.md ... Done.
            >>> co.update_references(orcid_id, recent_years=5, verbose=True)
            To write/update references in README.md
            ? [No]|Yes: yes
            Updating "Recent publications" in README.md ... Done.
        """

        file_path_ = _add_slashes(file_path)
        if _confirmed(f"To write/update references in {file_path_}\n?", confirmation_required):
            if verbose:
                print(f'Updating "{heading}" in {file_path_}', end=" ... ")

            try:
                references = self.fetch_references(
                    orcid_id=orcid_id, work_types=work_types, recent_years=recent_years,
                    style=style)

                if not os.path.exists(file_path):
                    with open(file_path, "w"):  # Create the file if it doesn't exist
                        pass

                self._update_references(
                    references=references, file_path=file_path, heading=heading,
                    heading_level=heading_level, heading_suffix=heading_suffix)

                if verbose:
                    print("Done.")

            except Exception as e:
                _print_failure_message(
                    e, prefix="Failed. Error:", verbose=verbose, raise_error=raise_error)
