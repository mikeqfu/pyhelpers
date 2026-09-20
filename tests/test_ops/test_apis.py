"""
Tests the :mod:`~pyhelpers.ops.apis` submodule.
"""

import time
from unittest.mock import MagicMock

import pytest

from pyhelpers.ops.apis import *


def _fake_session(status_code, payload=None):
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = payload or {}
    response.__enter__.return_value = response  # `with session.get(...) as response`
    session = MagicMock()
    session.get.return_value = response
    return session


class TestCrossRefOrcid:

    # noinspection PyNestedDecorators
    @pytest.fixture(scope='class')
    @classmethod
    def co(cls):
        return CrossRefOrcid(my_name="Fu, Qian")

    # noinspection PyNestedDecorators
    @pytest.fixture(scope='class')
    @classmethod
    def orcid_id(cls):
        return '0000-0002-6502-9934'

    def test_init(self, co):
        assert co.my_name == "Fu, Qian"

    def test_get_orcid_profile(self, co, orcid_id, capfd):
        profile_data: dict = co.get_orcid_profile(orcid_id)
        assert list(profile_data.keys()) == [
            'orcid-identifier',
            'preferences',
            'history',
            'person',
            'activities-summary',
            'path']

        profile_data = co.get_orcid_profile(orcid_id, section='unknown', verbose=True)
        out, _ = capfd.readouterr()
        assert profile_data is None and out.startswith("Error:")

    def test_get_list_of_works(self, co, orcid_id):
        list_of_works = co.get_list_of_works(orcid_id)
        assert isinstance(list_of_works, list)

    def test__get_zenodo_metadata(self, co, mocker):
        doi = '10.5281/zenodo.4017438'
        payload = {"metadata": {
            "resource_type": {"title": "Software"},
            "creators": [{"name": "Fu, Qian"}],
        }}

        mocker.patch(
            "pyhelpers.ops.apis._init_requests_session",
            return_value=_fake_session(200, payload)
        )
        metadata = co._get_zenodo_metadata(doi)
        assert metadata['journal'] == "Software"
        assert metadata['publisher'] == "Zenodo"
        assert metadata['authors'] == "Fu, Qian"

        # Non-200 responses give an empty dict
        mocker.patch(
            "pyhelpers.ops.apis._init_requests_session",
            return_value=_fake_session(404)
        )
        assert co._get_zenodo_metadata(doi + '123') == {}

    @pytest.mark.network
    def test__get_zenodo_metadata_live(self, co):
        metadata = co._get_zenodo_metadata('10.5281/zenodo.4017438')
        if not metadata:
            pytest.skip("Zenodo API returned a non-200 response")
        assert metadata['publisher'] == "Zenodo"

    def test_get_metadata_from_doi(self, co):
        doi = 'https://doi.org/10.1016/j.jii.2024.100729'
        metadata = co.get_metadata_from_doi(doi)
        assert isinstance(metadata, dict)
        assert metadata['authors'] == 'Fu, Qian, Nicholson, Gemma L., Easton, John M.'

    def test_format_references(self, co, orcid_id):
        ref_data = co.fetch_orcid_works(orcid_id)  # Past two years
        for style in ['APA', 'MLA', 'Chicago', 'Harvard', 'IEEE', 'Vancouver']:
            references = co.format_references(ref_data, style=style)
            assert any(f'**{co.my_name[:5]}' in ref for ref in references)

    @pytest.mark.parametrize('work_types', [None, ['journal', 'conference paper']])
    @pytest.mark.parametrize('recent_years', [1, 2])
    def test_fetch_references(self, co, orcid_id, work_types, recent_years):
        references = co.fetch_references(
            orcid_id=orcid_id, work_types=work_types, recent_years=recent_years)
        time.sleep(2)
        if len(references) > 0:
            assert any(f'**{co.my_name[:5]}' in ref for ref in references)

    @pytest.mark.parametrize('max_entries', [100, 2])
    def test_update_references(self, co, orcid_id, max_entries, tmp_path, monkeypatch, capfd):
        file_path = tmp_path / "README.md"

        monkeypatch.setattr('builtins.input', lambda _: "Yes")
        co.update_references(orcid_id, file_path=file_path, max_entries=max_entries, verbose=True)

        out, _ = capfd.readouterr()
        assert '"Recent publications"' in out and "README.md" in out and "Done." in out


if __name__ == '__main__':
    pytest.main()
