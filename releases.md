### Release history

<br/>

#### **[1.3.2](https://github.com/mikeqfu/pyhelpers/releases/tag/1.3.2)**

(*14 March 2022*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.3.1...1.3.2) since [1.3.1](https://pypi.org/project/pyhelpers/1.3.1/):**

- Added the following new functions: 
  - [xlsx_to_csv()](https://github.com/mikeqfu/pyhelpers/commit/7871eadbe0358ec1c48430fa9f671e5d93741343) to the module [store](https://github.com/mikeqfu/pyhelpers/blob/79a979462b492b5529448ae53291cc5555ced43f/pyhelpers/store.py);
  - [np_shift()](https://github.com/mikeqfu/pyhelpers/commit/e41df8b9da04f571bd53ac3df79a9de27a53521a) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/79a979462b492b5529448ae53291cc5555ced43f/pyhelpers/ops.py);
  - [project_point_to_line()](https://github.com/mikeqfu/pyhelpers/commit/e0b74756e6dba5697da758655d46f9cafeb1bbc7#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R326-R376) and [find_shortest_path()](https://github.com/mikeqfu/pyhelpers/commit/e0b74756e6dba5697da758655d46f9cafeb1bbc7#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R679-R785) to the module [geom](https://github.com/mikeqfu/pyhelpers/blob/79a979462b492b5529448ae53291cc5555ced43f/pyhelpers/geom.py).

**For more information and detailed specifications, check out [PyHelpers 1.3.2 documentation](https://pyhelpers.readthedocs.io/en/1.3.2/).**

<br/>

#### **[1.3.1](https://github.com/mikeqfu/pyhelpers/releases/tag/1.3.1)**

(*10 February 2022*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.3.0...1.3.1) since [1.3.0](https://pypi.org/project/pyhelpers/1.3.0/):**

- [Changed LICENSE to GPLv3+](https://github.com/mikeqfu/pyhelpers/commit/347ade14cd2c56ef1ed017a535a2be8172b3569c).
- Renamed the following functions: 
  - [~~save()~~](https://github.com/mikeqfu/pyhelpers/commit/7002573fb3530b55ac84b1a35c568200aa58a0ec#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L105) to [save_data()](https://github.com/mikeqfu/pyhelpers/commit/7002573fb3530b55ac84b1a35c568200aa58a0ec#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R765) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/d882fb31b1ffc41433f32b4b18f62e7840348aa7/pyhelpers/store.py);
  - [~~get_user_agent_strings()~~](https://github.com/mikeqfu/pyhelpers/commit/3e63df02271e8a9cedce0e1ebdfc36d517688249#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL1601) to [load_user_agent_strings()](https://github.com/mikeqfu/pyhelpers/commit/3e63df02271e8a9cedce0e1ebdfc36d517688249#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR1601) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/d882fb31b1ffc41433f32b4b18f62e7840348aa7/pyhelpers/ops.py).
- Improved the functions:
  - [remove_punctuation()](https://github.com/mikeqfu/pyhelpers/commit/926766a1be452644323c07b3e57e2409f99fa236#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R68), [find_similar_str()](https://github.com/mikeqfu/pyhelpers/commit/926766a1be452644323c07b3e57e2409f99fa236#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R190) and [convert_md_to_rst()](https://github.com/mikeqfu/pyhelpers/commit/8929bca83edfaf057affb05f55f0814853248bc0#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R627) in the module [text](https://github.com/mikeqfu/pyhelpers/blob/d882fb31b1ffc41433f32b4b18f62e7840348aa7/pyhelpers/text.py);
  - [merge_dicts()](https://github.com/mikeqfu/pyhelpers/commit/a32355e8041d904b604b4e2dc1534a0322121e12#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR796) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/d882fb31b1ffc41433f32b4b18f62e7840348aa7/pyhelpers/ops.py).
- Added [a few constants](https://github.com/mikeqfu/pyhelpers/commit/f35145ffea30837cf0851c84011dc9af0e59da91) cached as the package/module is imported.
- Added the following new functions/methods: 
  - [load_csv()](https://github.com/mikeqfu/pyhelpers/commit/5793d4279cc52acb4489281e119ba8829ba88529#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R1070-R1160) and [load_data()](https://github.com/mikeqfu/pyhelpers/commit/7002573fb3530b55ac84b1a35c568200aa58a0ec#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R1176-R1236) to the module [store](https://github.com/mikeqfu/pyhelpers/blob/d882fb31b1ffc41433f32b4b18f62e7840348aa7/pyhelpers/store.py);
  - [numeral_english_to_arabic()](https://github.com/mikeqfu/pyhelpers/commit/3d0ef9f892ff329e091714aacddbf6445ce384c5) to the module [text](https://github.com/mikeqfu/pyhelpers/blob/d882fb31b1ffc41433f32b4b18f62e7840348aa7/pyhelpers/text.py);
  - [PostgreSQL.list_schema_names()](https://github.com/mikeqfu/pyhelpers/commit/cb547e0ce2da90760c02fd461335a11e4db31185#diff-402d385f94d69cd9596a357c63ccdf2d12f55165339af5d3c1bd554fb5a5e146R785-R855) to the module [dbms](https://github.com/mikeqfu/pyhelpers/blob/d882fb31b1ffc41433f32b4b18f62e7840348aa7/pyhelpers/dbms.py);
  - [find_executable()](https://github.com/mikeqfu/pyhelpers/commit/a32355e8041d904b604b4e2dc1534a0322121e12#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR314-R356) and [compare_dicts()](https://github.com/mikeqfu/pyhelpers/commit/a32355e8041d904b604b4e2dc1534a0322121e12#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR749-R793) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/d882fb31b1ffc41433f32b4b18f62e7840348aa7/pyhelpers/ops.py).

**For more information and detailed specifications, check out [PyHelpers 1.3.1 documentation](https://pyhelpers.readthedocs.io/en/1.3.1/).**

<br/>

#### **[1.3.0](https://github.com/mikeqfu/pyhelpers/releases/tag/1.3.0)**

(*6 January 2022*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.18...1.3.0) since [1.2.18](https://pypi.org/project/pyhelpers/1.2.18/):**

- Renamed the module [~~sql~~](https://github.com/mikeqfu/pyhelpers/commit/edeb899b53ec9ba3b08e0e328f30bddcf064f0e5) to [dbms](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/dbms.py).
- Renamed the following functions: 
  - in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/dir.py):
    - [~~validate_input_data_dir()~~](https://github.com/mikeqfu/pyhelpers/commit/ff821197e1e5bedda1893e63a0985c15c6eea6eb#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09L245) to [validate_dir()](https://github.com/mikeqfu/pyhelpers/commit/ff821197e1e5bedda1893e63a0985c15c6eea6eb#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R245);
  - in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/ops.py):
    - [~~update_nested_dict()~~](https://github.com/mikeqfu/pyhelpers/commit/a4f3f617091587ce8aa83efca2fecfe1adaff8d6#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL442) to [update_dict()](https://github.com/mikeqfu/pyhelpers/commit/a4f3f617091587ce8aa83efca2fecfe1adaff8d6#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR442);
    - [~~get_all_values_from_nested_dict()~~](https://github.com/mikeqfu/pyhelpers/commit/a4f3f617091587ce8aa83efca2fecfe1adaff8d6#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL516) to [get_dict_values()](https://github.com/mikeqfu/pyhelpers/commit/a4f3f617091587ce8aa83efca2fecfe1adaff8d6#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR516);
    - [~~remove_multiple_keys_from_dict()~~](https://github.com/mikeqfu/pyhelpers/commit/a4f3f617091587ce8aa83efca2fecfe1adaff8d6#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL575) to [remove_dict_keys()](https://github.com/mikeqfu/pyhelpers/commit/a4f3f617091587ce8aa83efca2fecfe1adaff8d6#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR638);
    - [~~instantiate_requests_session()~~](https://github.com/mikeqfu/pyhelpers/commit/dc3817d0ff2e816276ecd8241f43c9c3a59b3927#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL1468) to [init_requests_session()](https://github.com/mikeqfu/pyhelpers/commit/dc3817d0ff2e816276ecd8241f43c9c3a59b3927#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR1468).
- Improved the following functions/class:
  - [PostgreSQL](https://github.com/mikeqfu/pyhelpers/commit/f23e534a9d0f65dcf695ca30ebaa766cae80fae3) in the module [dbms](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/dbms.py) (previously [~~sql~~](https://github.com/mikeqfu/pyhelpers/blob/fc6191fa37655fc664e6c74e15bcb4280e7bf5c1/pyhelpers/sql.py));
  - [wgs84_to_osgb36()](https://github.com/mikeqfu/pyhelpers/commit/18f1299356c53072536e9f983e5d36b00f73a184#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R89) and [osgb36_to_wgs84()](https://github.com/mikeqfu/pyhelpers/commit/18f1299356c53072536e9f983e5d36b00f73a184#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R153) in the module [geom](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/geom.py).
  - [parse_size()](https://github.com/mikeqfu/pyhelpers/commit/77abafb23312b57a034f0731ca8085dfeb2573b9) (newly added), [init_requests_session()](https://github.com/mikeqfu/pyhelpers/commit/6bde35cd84542403cc9a4d86976d5f33447ba0aa) and [download_file_from_url()](https://github.com/mikeqfu/pyhelpers/commit/898cba204f520daf459f770ba75cbc5af805440d) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/ops.py);
  - [load_json()](https://github.com/mikeqfu/pyhelpers/commit/adcb314be54daf4f19ed97c0df0e7fe61332fa2f) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/store.py);
  - [find_similar_str()](https://github.com/mikeqfu/pyhelpers/commit/d1c4cd872a00e3c94343241a14610ea3dc9ccb15#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R185) in the module [text](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/text.py);
- Added the following functions to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/01e90ddc9824c7e15ce92ef2ae833a9be760cb3e/pyhelpers/ops.py): [parse_size()](https://github.com/mikeqfu/pyhelpers/commit/295e60e9b38fab23896f5552986ba29c83f30e4d), [get_number_of_chunks()](https://github.com/mikeqfu/pyhelpers/commit/ec6d7a19a8a25e463ede05bbd3d5043217eb116f), [loop_in_pairs()](https://github.com/mikeqfu/pyhelpers/commit/cc26add9f3c269bb44b638f72602b7fa71e16e93), [is_url()](https://github.com/mikeqfu/pyhelpers/commit/a61e88abff2aa0028470fd7d538cac8688b1cd1c) and [update_dict_keys()](https://github.com/mikeqfu/pyhelpers/commit/a4f3f617091587ce8aa83efca2fecfe1adaff8d6#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR516-R576).
- Reduced the number of essential dependencies.

**For more information and detailed specifications, check out [PyHelpers 1.3.0 documentation](https://pyhelpers.readthedocs.io/en/1.3.0/).**

<br/>

#### **[1.2.18](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.18)**

(*20 October 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.17...1.2.18) since [1.2.17](https://pypi.org/project/pyhelpers/1.2.17/):**

- Improved the module [ops](https://github.com/mikeqfu/pyhelpers/blob/b4b822f71e03ea79ba4e663f2a20b772ce5824bd/pyhelpers/ops.py) by:
  - fixing the issue in [fake_requests_headers()](https://github.com/mikeqfu/pyhelpers/commit/69adc0e7fdea6175c7ab6a9013470d541d96e3e2#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL1248-R1376) that may occasionally raise [IndexError](https://docs.python.org/3/library/exceptions.html#IndexError);
  - adding a new function [get_fake_user_agent()](https://github.com/mikeqfu/pyhelpers/commit/b4b822f71e03ea79ba4e663f2a20b772ce5824bd#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL1227-R1276).

**For more information and detailed specifications, check out [PyHelpers 1.2.18 documentation](https://pyhelpers.readthedocs.io/en/1.2.18/).**

<br/>

#### **[1.2.17](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.17)**

(*1 October 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.16...1.2.17) since [1.2.16](https://pypi.org/project/pyhelpers/1.2.16/):**

- Improved the function [fake_requests_headers()](https://github.com/mikeqfu/pyhelpers/commit/39bf5c3bac09333f5ba043113dcbcc2706259ac6) to avoid raising [IndexError](https://docs.python.org/3/library/exceptions.html#IndexError).

**For more information and detailed specifications, check out [PyHelpers 1.2.17 documentation](https://pyhelpers.readthedocs.io/en/1.2.17/).**

<br/>

#### **[1.2.16](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.16)**

(*20 September 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.15...1.2.16) since [1.2.15](https://pypi.org/project/pyhelpers/1.2.15/):**

- Renamed the function [~~is_dirname()~~](https://github.com/mikeqfu/pyhelpers/commit/ebed45b34b276967ae34d893dd99f16cdce769d9#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09L213) to [is_dir()](https://github.com/mikeqfu/pyhelpers/commit/ebed45b34b276967ae34d893dd99f16cdce769d9#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R213) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/dir.py).
- Improved the following functions (with bug fixes):
  - [cd()](https://github.com/mikeqfu/pyhelpers/commit/a5be65408bca0a6aa279d7f785d22d27d2b6b277#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09L15-R67) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/dir.py);
  - [find_closest_points()](https://github.com/mikeqfu/pyhelpers/commit/19423013ec565425f0c3dac8ffc50cceced14975#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8L688-R805) in the module [geom](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/geom.py);
  - [confirmed()](https://github.com/mikeqfu/pyhelpers/commit/591692b9ae4cb519a9d01a72589dfff40a1dffe9#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL27-R75), [swap_cols()](https://github.com/mikeqfu/pyhelpers/commit/01948e89afb2bc04276f3e64012e9142feceb83b#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL618-R698), [swap_rows()](https://github.com/mikeqfu/pyhelpers/commit/01948e89afb2bc04276f3e64012e9142feceb83b#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL662-R740), [fake_requests_headers()](https://github.com/mikeqfu/pyhelpers/commit/ff01488ee709dadfb2d1de07af18459d9a111cda#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL1109-R1156) and  [download_file_from_url()](https://github.com/mikeqfu/pyhelpers/commit/40e819510600d6b7a65d6b76692686cf131c6189#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL1282-R1401) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/ops.py);
  - all the [functions](https://github.com/mikeqfu/pyhelpers/commit/e997ab9c6ff17201795b376ffafd4e0357c0fe41) in the module [settings](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/settings.py);
  - [save_multiple_spreadsheets()](https://github.com/mikeqfu/pyhelpers/commit/8ec18ccec49cf7ef7df80b9432afca3890699e8f#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L316-R462), [save_json()](https://github.com/mikeqfu/pyhelpers/commit/8ec18ccec49cf7ef7df80b9432afca3890699e8f#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L446-R523) and [load_json()](https://github.com/mikeqfu/pyhelpers/commit/8ec18ccec49cf7ef7df80b9432afca3890699e8f#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L904-R1007) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/store.py);
  - [find_similar_str()](https://github.com/mikeqfu/pyhelpers/commit/c4dd51fdec5b910d4ec6d800875dba5504aead0e#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127L148-R241) in the module [text](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/text.py).
- Added the following new functions:
  - [go_from_altered_cwd()](https://github.com/mikeqfu/pyhelpers/commit/a9e417669159bc7cc447cd966ee67120fffaf719#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R70-R117) to the module [dir](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/dir.py);
  - [drop_axis()](https://github.com/mikeqfu/pyhelpers/commit/c141b6537f900e9f2ae595438af4a83e089fb4dd#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R426-R505) to the module [geom](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/geom.py);
  - [instantiate_requests_session()](https://github.com/mikeqfu/pyhelpers/commit/82a307959c0c6daee09cad0128132850c5ea22da#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR1143-R1194) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/ops.py);
  - [save_joblib()](https://github.com/mikeqfu/pyhelpers/commit/3c4c5dec9095f56af2d7f668f19351c0010426bc#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R242-R279) and [load_joblib()](https://github.com/mikeqfu/pyhelpers/commit/3c4c5dec9095f56af2d7f668f19351c0010426bc#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R895-R946) to the module [store](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/store.py).

**For more information and detailed specifications, check out [PyHelpers 1.2.16 documentation](https://pyhelpers.readthedocs.io/en/1.2.16/).**

<br/>

#### **[1.2.15](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.15)**

(*19 April 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.14...1.2.15) since [1.2.14](https://pypi.org/project/pyhelpers/1.2.14/):**

- Improved the following functions/methods with bug fixes:
  - [find_similar_str()](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/text.py#L148-L232) and [convert_md_to_rst()](https://github.com/mikeqfu/pyhelpers/commit/a8dc317e359c61195509b23a96fed06e807653a6) in the module [text](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/text.py); 
  - [download_file_from_url()](https://github.com/mikeqfu/pyhelpers/commit/b731d329eca2fa39dc6ae934030223b22abb5ff3#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR1116-R1201) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/ops.py);
  - [save_svg_as_emf()](https://github.com/mikeqfu/pyhelpers/commit/82aefd81d07c2f5d1043d74a92522e34a79b456b) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/store.py);
  - [PostgreSQL.import_data()](https://github.com/mikeqfu/pyhelpers/commit/57df1b9a91f6ff87542f8ce4045ef3e7b036885f#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaL1163-R1233) and [PostgreSQL.drop_schema()](https://github.com/mikeqfu/pyhelpers/commit/66c9199c409499cab8b3c4e2ef7cabc3d826af6b) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/66c9199c409499cab8b3c4e2ef7cabc3d826af6b/pyhelpers/sql.py).
- Added a new function [is_downloadable()](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/ops.py#L1084-L1113) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/ops.py).

**For more information and detailed specifications, check out [PyHelpers 1.2.15 documentation](https://pyhelpers.readthedocs.io/en/1.2.15/).**

<br/>

#### **[1.2.14](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.14)**

(*27 March 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.13...1.2.14) since [1.2.13](https://pypi.org/project/pyhelpers/1.2.13/):**

- Rectified [an error](https://github.com/mikeqfu/pyhelpers/commit/bad3ff51a90a0da9ce9ebb2b4e20b3517204e05c) in the specification of dependencies for package installation.

**For more information and detailed specifications, check out [PyHelpers 1.2.14 documentation](https://pyhelpers.readthedocs.io/en/1.2.14/).**

<br/>

#### **[1.2.13](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.13)**

(*26 March 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.12...1.2.13) since [1.2.12](https://pypi.org/project/pyhelpers/1.2.12/):**

- Improved the module [sql](https://github.com/mikeqfu/pyhelpers/blob/c96c6acd31d7d94a99bb4591a741c656982868c9/pyhelpers/sql.py) with [a bug fix](https://github.com/mikeqfu/pyhelpers/commit/c96c6acd31d7d94a99bb4591a741c656982868c9) for errors raised when importing SQLAlchemy 1.4.0+.

**For more information and detailed specifications, check out [PyHelpers 1.2.13 documentation](https://pyhelpers.readthedocs.io/en/1.2.13/).** 

<br/>

#### **[1.2.12](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.12)**

(*22 March 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.11...1.2.12) since [1.2.11](https://pypi.org/project/pyhelpers/1.2.11/):**

- Resolved [an issue](https://github.com/mikeqfu/pyhelpers/commit/b426b761297117aeb599836f88bde0c08a5a50cf) that failed importing modules (after updating or reinstalling the package).
- Added a new function [gps_to_utc()](https://github.com/mikeqfu/pyhelpers/commit/b0338189cf16d5aac8c6a2d1785e37f7f3ae9f05) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/294fdb7d9817a58a6dd4cad909f23a9f75416e49/pyhelpers/ops.py).

**For more information and detailed specifications, check out [PyHelpers 1.2.12 documentation](https://pyhelpers.readthedocs.io/en/1.2.12/).** 

<br/>

#### **[1.2.11](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.11)**

(*3 March 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.10...1.2.11) since [1.2.10](https://pypi.org/project/pyhelpers/1.2.10/):**

- Fixed a bug in the method [PostgreSQL.import_data()](https://github.com/mikeqfu/pyhelpers/commit/e6b0a13481bb53a63a5b3884830889ce5adb611c) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/e6b0a13481bb53a63a5b3884830889ce5adb611c/pyhelpers/sql.py).

**For more information and detailed specifications, check out [PyHelpers 1.2.11 documentation](https://pyhelpers.readthedocs.io/en/1.2.11/).** 

<br/>

#### **[1.2.10](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.10)**

(*1 February 2021*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.9...1.2.10) since [1.2.9](https://pypi.org/project/pyhelpers/1.2.9/):**

- Improved the following functions/method with bug fixes to:
  - [np_preferences()](https://github.com/mikeqfu/pyhelpers/commit/ca9ba36da9671593adb752f2301debcf03beb99c#diff-8e1ccefca5009c849b1e96129b63e9dc483acfa1049605b6872c49e549d71793R15) in the module [settings](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/settings.py);
  - [save_multiple_spreadsheets()](https://github.com/mikeqfu/pyhelpers/commit/b96306545986a1c2763afb1aadcaf867695537b9#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R311) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/store.py);
  - [PostgreSQL.read_sql_query()](https://github.com/mikeqfu/pyhelpers/commit/5a8f251b570f0877d117251ec3e3408dba648398) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/sql.py).
- Added new functions/methods:
  - [eval_dtype()](https://github.com/mikeqfu/pyhelpers/commit/3e81a060b6ff967a93a47934f023a73b1e5ff79a#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR116), [swap_cols()](https://github.com/mikeqfu/pyhelpers/commit/8112735f33491ff91dfa5dc0564bda1f16e92b93#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR593) and [swap_rows()](https://github.com/mikeqfu/pyhelpers/commit/8112735f33491ff91dfa5dc0564bda1f16e92b93#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR635) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/ops.py);
  - [get_rectangle_centroid()](https://github.com/mikeqfu/pyhelpers/commit/bf248d6e1352f5d83e009d68189926bf6cfc4a03) to the module [geom](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/geom.py);
  - [.list_table_names()](https://github.com/mikeqfu/pyhelpers/commit/958942476652ca6202180ad6fd9c5eb8dfd72f22#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaR936) and [.alter_table_schema()](https://github.com/mikeqfu/pyhelpers/commit/958942476652ca6202180ad6fd9c5eb8dfd72f22#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaR995) to the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/958942476652ca6202180ad6fd9c5eb8dfd72f22/pyhelpers/sql.py#L54) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/sql.py).

**For more information and detailed specifications, check out [PyHelpers 1.2.10 documentation](https://pyhelpers.readthedocs.io/en/1.2.10/).**

<br/>

#### **[1.2.9](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.9)**

(*5 January 2021*)

*Note that the release **~~1.2.8~~** had been permanently deleted.*

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.7...1.2.9) since [1.2.7](https://pypi.org/project/pyhelpers/1.2.7/):**

- Made modifications with bug fixes to the following functions/class:
  - [validate_input_data_dir()](https://github.com/mikeqfu/pyhelpers/commit/f81c92d613a44272b61ee0d8fee085628e2e0880) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/dir.py);
  - [confirmed()](https://github.com/mikeqfu/pyhelpers/commit/eb1fa9b79a3c696c29fb0b5457fbc135cb49503e#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR23) and [fake_requests_headers()](https://github.com/mikeqfu/pyhelpers/commit/ce1caaef6bf306a5a0e4014f38ed1c0a159ff529#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR887) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/ops.py);
  - [PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/f43192408c548ad3d60df196d36dd970f022f954/pyhelpers/sql.py#L54) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/sql.py).
- Added new functions:
  - [get_obj_attr()](https://github.com/mikeqfu/pyhelpers/commit/9f10906069fbbb20261d1ea53685d2938c689fc6) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/ops.py);
  - [get_db_address()](https://github.com/mikeqfu/pyhelpers/commit/7215f14c0ff284cb86a29d001b2b72bec995fa83) to the module [sql](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/sql.py).

<br/>

#### **[1.2.7](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.7)**

(*17 November 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.6...1.2.7) since [1.2.6](https://pypi.org/project/pyhelpers/1.2.6/):**

- Fixed a minor bug in the method [PostgreSQL.import_data()](https://github.com/mikeqfu/pyhelpers/commit/c67a660f811d9ec370b45b9782fb7cb34d2e34c0) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/cd74ab1de677a40fb903947ff79aa99457a69f0b/pyhelpers/sql.py)
- Added new functions: 
  - [merge_dicts()](https://github.com/mikeqfu/pyhelpers/commit/14c639d1f956102e8f8f00017a5f4b52626ce5ba#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR324), [is_network_connected()](https://github.com/mikeqfu/pyhelpers/commit/14c639d1f956102e8f8f00017a5f4b52626ce5ba#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR770) and [is_url_connectable()](https://github.com/mikeqfu/pyhelpers/commit/14c639d1f956102e8f8f00017a5f4b52626ce5ba#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR790) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/cd74ab1de677a40fb903947ff79aa99457a69f0b/pyhelpers/ops.py);
  - [get_acronym()](https://github.com/mikeqfu/pyhelpers/commit/246e6a1e73c8d072f9f6c2120e92e11406263b40#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R61) and [extract_words1upper()](https://github.com/mikeqfu/pyhelpers/commit/246e6a1e73c8d072f9f6c2120e92e11406263b40#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R107) to the module [text](https://github.com/mikeqfu/pyhelpers/blob/cd74ab1de677a40fb903947ff79aa99457a69f0b/pyhelpers/text.py).

<br/>

#### **[1.2.6](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.6)**

(*6 November 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.5...1.2.6) since [1.2.5](https://pypi.org/project/pyhelpers/1.2.5/):**

- Renamed two functions in the module [geom](https://github.com/mikeqfu/pyhelpers/blob/ba2370b8511a06763076033546a24dd60ec23927/pyhelpers/geom.py):
  - [~~find_closest_point_from()~~](https://github.com/mikeqfu/pyhelpers/commit/ba2370b8511a06763076033546a24dd60ec23927#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8L730) to [find_closest_point()](https://github.com/mikeqfu/pyhelpers/blob/ba2370b8511a06763076033546a24dd60ec23927/pyhelpers/geom.py#L550);
  - [~~find_closest_points_between()~~](https://github.com/mikeqfu/pyhelpers/commit/ba2370b8511a06763076033546a24dd60ec23927#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8L793) to [find_closest_points()](https://github.com/mikeqfu/pyhelpers/blob/ba2370b8511a06763076033546a24dd60ec23927/pyhelpers/geom.py#L613).
- Reduced the number of essential dependencies for installing the package (see also the [installation note](https://pyhelpers.readthedocs.io/en/1.2.6/installation.html)).
- Enabled direct access to all functions/classes from importing the package without having to specifying the modules they reside in.
- Fixed [a minor bug](https://github.com/mikeqfu/pyhelpers/commit/0db725542cef75889889b1e401f0db8eaf07188d) in the function [fake_requests_headers()](https://github.com/mikeqfu/pyhelpers/blob/0db725542cef75889889b1e401f0db8eaf07188d/pyhelpers/ops.py#L739) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/0db725542cef75889889b1e401f0db8eaf07188d/pyhelpers/ops.py).

<br/>

#### **[1.2.5](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.5)**

(*12 October 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.4...1.2.5) since [1.2.4](https://pypi.org/project/pyhelpers/1.2.4/):**

- Renamed the function [~~rm_dir()~~](https://github.com/mikeqfu/pyhelpers/commit/833da11ac0cc6920d85c92c6e1401ea37af96bf1#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09L206) to [delete_dir()](https://github.com/mikeqfu/pyhelpers/blob/833da11ac0cc6920d85c92c6e1401ea37af96bf1/pyhelpers/dir.py#L212) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/833da11ac0cc6920d85c92c6e1401ea37af96bf1/pyhelpers/dir.py).
- Moved the function [save_web_page_as_pdf()](https://github.com/mikeqfu/pyhelpers/commit/95d8a9502d19868fdaa747fd7662f0832b41ca7b#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127L417) from the module [text](https://github.com/mikeqfu/pyhelpers/blob/95d8a9502d19868fdaa747fd7662f0832b41ca7b/pyhelpers/text.py) to [store](https://github.com/mikeqfu/pyhelpers/blob/b33f1df08991264622dd20876d572851a8b7e5ec/pyhelpers/store.py#L691).
- Removed two functions from the module [ops](https://github.com/mikeqfu/pyhelpers/blob/c7e22ae0d2e20c9ab84e5224b300e0a660ccb2e0/pyhelpers/ops.py): [~~get_variable_name()~~](https://github.com/mikeqfu/pyhelpers/commit/c7e22ae0d2e20c9ab84e5224b300e0a660ccb2e0#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL165) and [~~get_variable_names()~~](https://github.com/mikeqfu/pyhelpers/commit/c7e22ae0d2e20c9ab84e5224b300e0a660ccb2e0#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL203).
- Improved the following function/class:
  - [save()](https://github.com/mikeqfu/pyhelpers/commit/b33f1df08991264622dd20876d572851a8b7e5ec#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R102) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/b33f1df08991264622dd20876d572851a8b7e5ec/pyhelpers/store.py);
  - [PostgreSQL](https://github.com/mikeqfu/pyhelpers/commit/116c7c1872fc8916856ae067e1edc89f8f8580bd) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/116c7c1872fc8916856ae067e1edc89f8f8580bd/pyhelpers/sql.py).

<br/>

#### **[1.2.4](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.4)**

(*7 September 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.3...1.2.4) since [1.2.3](https://pypi.org/project/pyhelpers/1.2.3/):**

- Improved the function [fake_requests_headers()](https://github.com/mikeqfu/pyhelpers/commit/0462c6bb3e3d32d6266ce2a713d99c90f8b5a0c6) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/ef9caca1e696f699633a4ee619e57c9f27ae6ce2/pyhelpers/ops.py).

<br/>

#### **[1.2.3](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.3)**

(*7 September 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.2...1.2.3) since [1.2.2](https://pypi.org/project/pyhelpers/1.2.2/):**

- Fixed a few bugs in the following functions/class:
  - [download_file_from_url()](https://github.com/mikeqfu/pyhelpers/commit/76f2f097cf2bad365f84bf9fa9ba8c97454fe7ee) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/d3e84b9af834d118d555ae0e41fb32ffa7355b9f/pyhelpers/ops.py);
  - [get_specific_filepath_info()](https://github.com/mikeqfu/pyhelpers/commit/e24a68f2ec80ef6316e1b0af4c68f779225ab2d8#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L62) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/e3f8ba9ffb775d030bde7aa18df131cf6e45b5b2/pyhelpers/store.py);
  - [PostgreSQL](https://github.com/mikeqfu/pyhelpers/commit/319fe94aac4f215b58620b23a7556489716b59fe) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/e3f8ba9ffb775d030bde7aa18df131cf6e45b5b2/pyhelpers/sql.py).
- Added a new function [fake_requests_headers()](https://github.com/mikeqfu/pyhelpers/blob/0257ca607d80fccfd291e93f0f311cb73b21f1d1/pyhelpers/ops.py#L19-L33) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/e3f8ba9ffb775d030bde7aa18df131cf6e45b5b2/pyhelpers/ops.py).

<br/>

#### **[1.2.2](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.2)**

(*18 July 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.1...1.2.2) since [1.2.1](https://pypi.org/project/pyhelpers/1.2.1/):**

- Improved the following functions: 
  - [get_specific_filepath_info()](https://github.com/mikeqfu/pyhelpers/blob/305d08a8e7bd9aa28698360cde6ca5120d8af2aa/pyhelpers/store.py#L16) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/33002edab79a3fc976b7ae7ded2f33547dc0e5f5/pyhelpers/store.py);
  - [split_list()](https://github.com/mikeqfu/pyhelpers/commit/aa387606d2bc02834933e94a7cbccbc1e545dafe#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL222) and [get_all_values_from_nested_dict()](https://github.com/mikeqfu/pyhelpers/commit/aa387606d2bc02834933e94a7cbccbc1e545dafe#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL341) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/33002edab79a3fc976b7ae7ded2f33547dc0e5f5/pyhelpers/ops.py).

<br/>

#### **[1.2.1](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.1)**

(*1 July 2020*)

*Note that the release **~~1.2.0~~** had been permanently deleted.*

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.1.2...1.2.1) since [1.1.2](https://pypi.org/project/pyhelpers/1.1.2/):**

- Integrated the module [~~download~~](https://github.com/mikeqfu/pyhelpers/commit/d36527279cad92941c92eaec38b5c4ba33119f19) into [ops](https://github.com/mikeqfu/pyhelpers/blob/4a3a0c9ac83440007136f504e44562ec75b973df/pyhelpers/ops.py) and made the following changes:
  - renamed the function [~~download()~~](https://github.com/mikeqfu/pyhelpers/commit/d36527279cad92941c92eaec38b5c4ba33119f19#diff-6f8fcaf7c0adfbc7a2f9590aa4d76d65bbe0f8f0b383509db21cf9f01a579155L9) to [download_file_from_url()](https://github.com/mikeqfu/pyhelpers/commit/0f6fb049e224398ae126ca2bf03cfeced8707480#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR18);
  - added a new function [convert_md_to_rst()](https://github.com/mikeqfu/pyhelpers/commit/82bf68e64e864efb95c728a894276367047c79fb#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R370);
  - improved the following functions: [split_list_by_size()](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL92), [split_list()](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL111), [get_extreme_outlier_bounds()](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL246), <br/>[interquartile_range()](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL268), [find_closest_date()](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL284) and [detect_nan_for_str_column()](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL392).
- Moved the function [save_web_page_as_pdf()](https://github.com/mikeqfu/pyhelpers/commit/82bf68e64e864efb95c728a894276367047c79fb#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R304) from the module [store](https://github.com/mikeqfu/pyhelpers/blob/fc4f4b4e00237fbb7648f96015af5c0ad34d490a/pyhelpers/store.py) to [text](https://github.com/mikeqfu/pyhelpers/blob/82bf68e64e864efb95c728a894276367047c79fb/pyhelpers/text.py).
- Improved the following functions/class:
  - [get_specific_filepath_info()](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L17), [save_fig()](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L423), [save_svg_as_emf()](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L469), [seven_zip()](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L626) and  [load_csr_matrix()](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L626) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/4a3a0c9ac83440007136f504e44562ec75b973df/pyhelpers/store.py);
  - [PostgreSQL](https://github.com/mikeqfu/pyhelpers/commit/4598e3e16d706f1cc4472d774ecd4dbf53d4eb28#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaL20) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/4a3a0c9ac83440007136f504e44562ec75b973df/pyhelpers/sql.py).

<br/>

#### **[1.1.2](https://github.com/mikeqfu/pyhelpers/releases/tag/1.1.2)**

(*30 May 2020*)

*Note that the release **~~1.1.1~~** had been permanently deleted.*

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.1.0...1.1.2) since [1.1.0](https://pypi.org/project/pyhelpers/1.1.0/):**

- Renamed the following function/method:
  - [~~save_excel()~~](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L114-L115) to [save_spreadsheet()](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R220-R265) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/store.py);
  - [~~.disconnect()~~](https://github.com/mikeqfu/pyhelpers/commit/ad67be119ee4f74b04803a7d73cbeafb74bbc63b#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaL124) to [.disconnect_database()](https://github.com/mikeqfu/pyhelpers/commit/ad67be119ee4f74b04803a7d73cbeafb74bbc63b#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaR126) of the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/sql.py#L20) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/sql.py).
- Removed the function [~~csr_matrix_to_dict()~~](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127L50-L58) from the module [text](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/text.py).
- Removed redundant parameters from functions in the module [store](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/store.py).
- Improved the following functions by adding optional parameters:
  - [cd()](https://github.com/mikeqfu/pyhelpers/commit/780b8bf50db0a265084ffcff91479c7d5c12bb4d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R11), [cdd()](https://github.com/mikeqfu/pyhelpers/commit/780b8bf50db0a265084ffcff91479c7d5c12bb4d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R32), [cd_data](https://github.com/mikeqfu/pyhelpers/commit/780b8bf50db0a265084ffcff91479c7d5c12bb4d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R56) and [rm_dir()](https://github.com/mikeqfu/pyhelpers/commit/780b8bf50db0a265084ffcff91479c7d5c12bb4d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R125) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/dir.py);
  - [download()](https://github.com/mikeqfu/pyhelpers/commit/860cfd69ddf26480af722f59018550c83763b091#diff-6f8fcaf7c0adfbc7a2f9590aa4d76d65bbe0f8f0b383509db21cf9f01a579155R10) in the module [download](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/download.py);
  - [save_svg_as_emf()](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R467) and [save_web_page_as_pdf()](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R501-R502) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/store.py).
- Added new functions: 
  - to the module [geom](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/geom.py): [sketch_square()](https://github.com/mikeqfu/pyhelpers/commit/3e412e536ead2346221b82cb2018f0577fdf03c0#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R681-R735);
  - to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/ops.py): [create_rotation_matrix()](https://github.com/mikeqfu/pyhelpers/commit/ff069a10f9f61c33ed43520a2b7bf20bd3c262ea#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR413-R425) and [dict_to_dataframe()](https://github.com/mikeqfu/pyhelpers/commit/3444c80cbb05789d623233206b1ebbf528227730#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR429-R439);
  - to the module [store](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/store.py): [save_multiple_spreadsheets()](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R268-R342), [load_multiple_spreadsheets()](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R345-R388), <br/>[unzip()](https://github.com/mikeqfu/pyhelpers/commit/df7614ad9d96b526394a4914d69bc6c3dfa34679#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R560-R589), [seven_zip()](https://github.com/mikeqfu/pyhelpers/commit/df7614ad9d96b526394a4914d69bc6c3dfa34679#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R592-R623) and [load_csr_matrix()](https://github.com/mikeqfu/pyhelpers/commit/df7614ad9d96b526394a4914d69bc6c3dfa34679#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R626-R649);
  - to the module [text](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/text.py): [remove_punctuation()](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R60-R78), [count_words()](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R81-R96), [calculate_idf()](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R99-R122), [calculate_tf_idf()](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R125-R138), <br/>[euclidean_distance_between_texts()](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R141-R168) and [cosine_similarity_between_texts()](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R171-R208).

<br/>

#### **[1.1.0](https://github.com/mikeqfu/pyhelpers/releases/tag/1.1.0)**

(*22 April 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.26...1.1.0) since [1.0.26](https://pypi.org/project/pyhelpers/1.0.26/):**

- Made [a few modifications](https://github.com/mikeqfu/pyhelpers/commit/eac4bc4a2a4665017f18452a89cbacf4fdecd6d7) to the class [sql.PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/2326cd2e11e8264bc96a71386755206123b554d1/pyhelpers/sql.py#L20) to speed up importing data into, and retrieving data from, a PostgreSQL database.
- Fixed [a minor bug](https://github.com/mikeqfu/pyhelpers/commit/de0cd35ead0224a7decda8527edb8bea816dd2a1#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127L42) in the function [text.find_matched_str()](https://github.com/mikeqfu/pyhelpers/blob/2326cd2e11e8264bc96a71386755206123b554d1/pyhelpers/text.py#L34).
- Improved the two modules [store](https://github.com/mikeqfu/pyhelpers/commit/79a2a01ce07c813a170643e2ba19c51a8e5c66e6) and [text](https://github.com/mikeqfu/pyhelpers/commit/de0cd35ead0224a7decda8527edb8bea816dd2a1).

<br/>

#### **[1.0.26](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.26)**

(*12 March 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.25...1.0.26) since [1.0.25](https://pypi.org/project/pyhelpers/1.0.25/):**

- Fixed [a few bugs](https://github.com/mikeqfu/pyhelpers/commit/96ffbafcdd27f245c3462c009f3cb66111f61ffa) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/6fe6c272bdb6042ec6040c6164d0d9b9554faf11/pyhelpers/store.py).

<br/>

#### **[1.0.25](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.25)**

(*6 March 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.24...1.0.25) since [1.0.24](https://pypi.org/project/pyhelpers/1.0.24/):**

- Improved the functions, [osgb36_to_wgs84()](https://github.com/mikeqfu/pyhelpers/commit/d8f6a36b2a6e1ec54ec0ec4faa637337f7542bd1#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R21-R25) and [wgs84_to_osgb36()](https://github.com/mikeqfu/pyhelpers/commit/d8f6a36b2a6e1ec54ec0ec4faa637337f7542bd1#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R42-R46), in the module [geom](https://github.com/mikeqfu/pyhelpers/blob/3f0baeae6c63f3afb8ea8cf1cdff35c9647c92f0/pyhelpers/geom.py).

<br/>

#### **[1.0.24](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.24)**

(*28 January 2020*)

*Note that the release **~~1.0.23~~** had been permanently deleted.*

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.22...1.0.24) since [1.0.22](https://pypi.org/project/pyhelpers/1.0.22/):**

- Fixed [a bug](https://github.com/mikeqfu/pyhelpers/commit/039c09ebaa879d5251ba967824bd12c317ed9206) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/383b226e0e27fb6622f405a62a016601bc844666/pyhelpers/sql.py).

<br/>

#### **[1.0.22](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.22)**

(*27 January 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.21...1.0.22) since [1.0.21](https://pypi.org/project/pyhelpers/1.0.21/):**

- Renamed the function [~~divide_list_into_chunks()~~](https://github.com/mikeqfu/pyhelpers/commit/afa60ee31793f619ee3979704ffc6709543241c8#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL88) to [split_list_by_size()](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/ops.py#L90) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/ops.py).
- Added two new functions to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/ops.py): [split_list()](https://github.com/mikeqfu/pyhelpers/commit/afa60ee31793f619ee3979704ffc6709543241c8#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR107-R122) and [split_iterable()](https://github.com/mikeqfu/pyhelpers/commit/afa60ee31793f619ee3979704ffc6709543241c8#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR125-R142).
- Improved the following function/class:
  - [gdal_configurations()](https://github.com/mikeqfu/pyhelpers/commit/0d8a461b89f0d8a917e52a491c17e8f6d0cbf3cf) in the module [settings](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/settings.py);
  - [PostgreSQL](https://github.com/mikeqfu/pyhelpers/commit/dfeaf212bbaa3ee05dd60d7fe9f6f33cc58e0ced) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/sql.py).

<br/>

#### **[1.0.21](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.21)**

(*20 January 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.20...1.0.21) since [1.0.20](https://pypi.org/project/pyhelpers/1.0.20/):**

- Added a new module [sql](https://github.com/mikeqfu/pyhelpers/blob/8f86efcee944b172eb9c525077b3b2425e5730ae/pyhelpers/sql.py).
- Added a new function [detect_nan_for_str_column()](https://github.com/mikeqfu/pyhelpers/commit/0c02a011193e36619c4ee1828fd15bd501b58025#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR320-R328) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/8f86efcee944b172eb9c525077b3b2425e5730ae/pyhelpers/ops.py).

<br/>

#### **[1.0.20](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.20)**

(*7 January 2020*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.19...1.0.20) since [1.0.19](https://pypi.org/project/pyhelpers/1.0.19/):**

- Fixed [a few minor bugs](https://github.com/mikeqfu/pyhelpers/commit/8ce0aa9bd7c285b1b936ae54fe6d51d386bdbf77) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/425184670493a3f5e4bf65fac1aac5232071f18b/pyhelpers/store.py).

<br/>

#### **[1.0.19](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.19)**

(*28 November 2019*)

*Note that the release **~~1.0.18~~** had been permanently deleted.*

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.17...1.0.19) since [1.0.17](https://pypi.org/project/pyhelpers/1.0.17/):**

- Renamed the module [~~misc~~](https://github.com/mikeqfu/pyhelpers/commit/65c0e41844989c5fecd0d114315002752ac1ce3c) to [ops](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/ops.py); moved the function [csr_matrix_to_dict()](https://github.com/mikeqfu/pyhelpers/commit/ad191ddacac3344182a875ebd13b7c36526d2eb9#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R50-R63) to the module [text](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/text.py).
- Fixed minor bugs:
  - [save_feather()](https://github.com/mikeqfu/pyhelpers/commit/78b446f0152a098553dc8b9c3c68ce0f655362e0) and [load_feather()](https://github.com/mikeqfu/pyhelpers/commit/151ca2f436363091b77a8b8cc1284e6956c7db97) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/store.py);
  - [download()](https://github.com/mikeqfu/pyhelpers/commit/937908d2953cbed4848a400d5f2530d4dfb02456) in the module [download](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/download.py); 
  - [mpl_preferences()](https://github.com/mikeqfu/pyhelpers/commit/73c7b66685a64147c998c03bd003d1f8d8c42eb3) in the module [settings](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/settings.py).
- Added new functions: 
  - [show_square()](https://github.com/mikeqfu/pyhelpers/commit/8abec1f3c522409fe72b4075b4a0188b261a5661#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R363-R384), [locate_square_vertices()](https://github.com/mikeqfu/pyhelpers/commit/8abec1f3c522409fe72b4075b4a0188b261a5661#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R387-R429) and [locate_square_vertices_calc()](https://github.com/mikeqfu/pyhelpers/commit/8abec1f3c522409fe72b4075b4a0188b261a5661#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R432-R472) to the module [geom](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/geom.py); 
  - [is_dirname()](https://github.com/mikeqfu/pyhelpers/commit/db7303b4dd4b92281f53c6a8a107efedeafb557d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R75-R95) to the module [dir](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/dir.py).
- Improved the module [store](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/store.py) with modifications to the functions: [save_pickle()](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R66), [load_pickle()](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R96), [save_json()](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R113), [load_json()](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R142) and [save()](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R204).

<br/>

#### **[1.0.17](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.17)**

(*10 September 2019*)

##### **Notable [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.16...1.0.17) since [1.0.16](https://pypi.org/project/pyhelpers/1.0.16/):**

- Improved the function [rm_dir()](https://github.com/mikeqfu/pyhelpers/commit/f3b4e1bb9654c2102bea524cb280c19030f80163#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R100-R121) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/3961ec9a2a2c15d60454551d758b20875cd02570/pyhelpers/dir.py).
- Tidied up the code of the three modules: [misc](https://github.com/mikeqfu/pyhelpers/commit/ffa1220c443e5d26587d6469104e5dde05d8e4e4), [geom](https://github.com/mikeqfu/pyhelpers/commit/d8a9b0defd7a4539a89b150250e26a2967924f9b) and [store](https://github.com/mikeqfu/pyhelpers/commit/36809752328e1bfe9a30bf67fd2e36c6f332009d).

<br/>

#### **[1.0.16](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.16)**

(*3 September 2019*)

This is a release of a **brand-new** version. 

*Note that the initial releases (of early versions up to **~~1.0.15~~**) had been permanently deleted.*
