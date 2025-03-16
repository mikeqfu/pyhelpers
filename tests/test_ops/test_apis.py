"""
Tests the :mod:`~pyhelpers.ops.apis` submodule.
"""

import tempfile
import time

import pytest

from pyhelpers.ops.apis import *


class TestCrossRefOrcid:

    @pytest.fixture(scope='class')
    def co(self):
        return CrossRefOrcid(my_name="Fu, Qian")

    @pytest.fixture(scope='class')
    def orcid_id(self):
        return '0000-0002-6502-9934'

    def test_init(self, co):
        assert co.my_name == "Fu, Qian"

    def test_get_orcid_profile(self, co, orcid_id, capfd):
        profile_data = co.get_orcid_profile(orcid_id)
        assert list(profile_data.keys()) == [
            'orcid-identifier',
            'preferences',
            'history',
            'person',
            'activities-summary',
            'path']

        profile_data = co.get_orcid_profile(orcid_id, section='unknown', verbose=True)
        out, _ = capfd.readouterr()
        assert profile_data is None
        assert out.startswith("Error:")

    def test_get_list_of_works(self, co, orcid_id):
        list_of_works = co.get_list_of_works(orcid_id)
        assert isinstance(list_of_works, list)

    def test__get_zenodo_metadata(self, co):
        doi = '10.5281/zenodo.4017438'
        metadata = co._get_zenodo_metadata(doi)
        assert metadata['journal'] == 'Software'
        assert metadata['publisher'] == 'Zenodo'

        metadata = co._get_zenodo_metadata(doi + '123')
        assert metadata == {}

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
        assert any(f'**{co.my_name[:5]}' in ref for ref in references)

    def test_update_references(self, co, orcid_id, monkeypatch, capfd):
        with tempfile.NamedTemporaryFile() as f:
            temp_file = f.name + '.md'

            monkeypatch.setattr('builtins.input', lambda _: "Yes")

            co.update_references(orcid_id, file_path=temp_file, verbose=True)

            out, _ = capfd.readouterr()
            assert "Updating" in out and "Done." in out

        os.remove(temp_file)


if __name__ == '__main__':
    pytest.main()
