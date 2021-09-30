### Release history



#### [1.2.16](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.16)

*20 September 2021*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.15...1.2.16) since [1.2.15](https://pypi.org/project/pyhelpers/1.2.15/):

- in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/dir.py):
  - added a new function [go_from_altered_cwd](https://github.com/mikeqfu/pyhelpers/commit/a9e417669159bc7cc447cd966ee67120fffaf719#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R70-R117)
  - modified the function [cd](https://github.com/mikeqfu/pyhelpers/commit/a5be65408bca0a6aa279d7f785d22d27d2b6b277#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09L15-R67)
  - renamed the function [~~is_dirname~~](https://github.com/mikeqfu/pyhelpers/commit/ebed45b34b276967ae34d893dd99f16cdce769d9#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09L213) to [is_dir](https://github.com/mikeqfu/pyhelpers/commit/ebed45b34b276967ae34d893dd99f16cdce769d9#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R213)
- in the module [geom](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/geom.py):
  - added a new function [drop_axis](https://github.com/mikeqfu/pyhelpers/commit/c141b6537f900e9f2ae595438af4a83e089fb4dd#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R426-R505)
  - modified the function [find_closest_points](https://github.com/mikeqfu/pyhelpers/commit/19423013ec565425f0c3dac8ffc50cceced14975#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8L688-R805)
- in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/ops.py):
  - added a new function [instantiate_requests_session](https://github.com/mikeqfu/pyhelpers/commit/82a307959c0c6daee09cad0128132850c5ea22da#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR1143-R1194)
  - modified the function [confirmed](https://github.com/mikeqfu/pyhelpers/commit/591692b9ae4cb519a9d01a72589dfff40a1dffe9#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL27-R75)
  - made modifications with bug fixes to the following functions:
    - [swap_cols](https://github.com/mikeqfu/pyhelpers/commit/01948e89afb2bc04276f3e64012e9142feceb83b#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL618-R698)
    - [swap_rows](https://github.com/mikeqfu/pyhelpers/commit/01948e89afb2bc04276f3e64012e9142feceb83b#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL662-R740)
    - [fake_requests_headers](https://github.com/mikeqfu/pyhelpers/commit/ff01488ee709dadfb2d1de07af18459d9a111cda#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL1109-R1156)
    - [download_file_from_url](https://github.com/mikeqfu/pyhelpers/commit/40e819510600d6b7a65d6b76692686cf131c6189#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL1282-R1401)
- in the module [store](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/store.py):
  - added the following two new functions: 
    - [save_joblib](https://github.com/mikeqfu/pyhelpers/commit/3c4c5dec9095f56af2d7f668f19351c0010426bc#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R242-R279)
    - [load_joblib](https://github.com/mikeqfu/pyhelpers/commit/3c4c5dec9095f56af2d7f668f19351c0010426bc#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R895-R946)
  - modified the following three functions: 
    - [save_multiple_spreadsheets](https://github.com/mikeqfu/pyhelpers/commit/8ec18ccec49cf7ef7df80b9432afca3890699e8f#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L316-R462)
    - [save_json](https://github.com/mikeqfu/pyhelpers/commit/8ec18ccec49cf7ef7df80b9432afca3890699e8f#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L446-R523)
    - [load_json](https://github.com/mikeqfu/pyhelpers/commit/8ec18ccec49cf7ef7df80b9432afca3890699e8f#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L904-R1007)
- made [modifications](https://github.com/mikeqfu/pyhelpers/commit/e997ab9c6ff17201795b376ffafd4e0357c0fe41) to all the functions in the module [settings](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/settings.py)
- modified the function [find_similar_str](https://github.com/mikeqfu/pyhelpers/commit/c4dd51fdec5b910d4ec6d800875dba5504aead0e#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127L148-R241) in the module [text](https://github.com/mikeqfu/pyhelpers/blob/4cdf763ba7cecb46d66fbf3ea4eb684e04500d0e/pyhelpers/text.py)

**For more information about the update and/or a full walk-through of this release, check out [PyHelpers 1.2.16 documentation](https://pyhelpers.readthedocs.io/en/1.2.16/).**



#### [1.2.15](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.15)

*19 April 2021*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.14...1.2.15) since [1.2.14](https://pypi.org/project/pyhelpers/1.2.14/):

- in the module [text](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/text.py):
  - modified the function [find_similar_str](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/text.py#L148-L232)
  - fixed [a minor bug](https://github.com/mikeqfu/pyhelpers/commit/a8dc317e359c61195509b23a96fed06e807653a6) in the function [convert_md_to_rst](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/text.py#L557-L622) 
- in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/ops.py):
  - modified the function [download_file_from_url](https://github.com/mikeqfu/pyhelpers/commit/b731d329eca2fa39dc6ae934030223b22abb5ff3#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR1116-R1201)
  - added a new function [is_downloadable](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/ops.py#L1084-L1113)
- in the module [store](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/store.py): 
  - fixed [a minor bug](https://github.com/mikeqfu/pyhelpers/commit/82aefd81d07c2f5d1043d74a92522e34a79b456b) in the function [save_svg_as_emf](https://github.com/mikeqfu/pyhelpers/blob/8b5d25875264a5cc0b397296ce12e9ff53300215/pyhelpers/store.py#L529-L610)
- in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/66c9199c409499cab8b3c4e2ef7cabc3d826af6b/pyhelpers/sql.py):
  - modified the method [PostgreSQL.import_data](https://github.com/mikeqfu/pyhelpers/commit/57df1b9a91f6ff87542f8ce4045ef3e7b036885f#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaL1163-R1233) and [import statements](https://github.com/mikeqfu/pyhelpers/commit/57df1b9a91f6ff87542f8ce4045ef3e7b036885f#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaL18-R18)
  - fixed [a bug](https://github.com/mikeqfu/pyhelpers/commit/66c9199c409499cab8b3c4e2ef7cabc3d826af6b) in the method [PostgreSQL.drop_schema](https://github.com/mikeqfu/pyhelpers/blob/66c9199c409499cab8b3c4e2ef7cabc3d826af6b/pyhelpers/sql.py#L666-L760)

**For more information about the update and/or a full walk-through of this release, check out [PyHelpers 1.2.15 documentation](https://pyhelpers.readthedocs.io/en/1.2.15/).**



#### [1.2.14](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.14)

*27 March 2021*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.13...1.2.14) since [1.2.13](https://pypi.org/project/pyhelpers/1.2.13/):

- rectified [an error](https://github.com/mikeqfu/pyhelpers/commit/bad3ff51a90a0da9ce9ebb2b4e20b3517204e05c) in the specification of dependencies for package installation

**For more information about the update and/or a full walk-through of this release, check out [PyHelpers 1.2.14 documentation](https://pyhelpers.readthedocs.io/en/1.2.14/).**



#### [1.2.13](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.13)

*26 March 2021*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.12...1.2.13) since [1.2.12](https://pypi.org/project/pyhelpers/1.2.12/):

- modified the module [sql](https://github.com/mikeqfu/pyhelpers/blob/c96c6acd31d7d94a99bb4591a741c656982868c9/pyhelpers/sql.py) with [a bug fix](https://github.com/mikeqfu/pyhelpers/commit/c96c6acd31d7d94a99bb4591a741c656982868c9) for errors raised when importing SQLAlchemy 1.4.0+

**For more information about the update and/or a full walk-through of this release, check out [PyHelpers 1.2.13 documentation](https://pyhelpers.readthedocs.io/en/1.2.13/).** 



#### [1.2.12](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.12)

*22 March 2021*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.11...1.2.12) since [1.2.11](https://pypi.org/project/pyhelpers/1.2.11/):

- resolved [an issue](https://github.com/mikeqfu/pyhelpers/commit/b426b761297117aeb599836f88bde0c08a5a50cf) that failed importing modules (after updating or reinstalling the package)
- added a new function [gps_to_utc](https://github.com/mikeqfu/pyhelpers/commit/b0338189cf16d5aac8c6a2d1785e37f7f3ae9f05) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/294fdb7d9817a58a6dd4cad909f23a9f75416e49/pyhelpers/ops.py)

**For more information about the update and/or a full walk-through of this release, check out [PyHelpers 1.2.12 documentation](https://pyhelpers.readthedocs.io/en/1.2.12/).** 



#### [1.2.11](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.11)

*3 March 2021*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.10...1.2.11) since [1.2.10](https://pypi.org/project/pyhelpers/1.2.10/):

- fixed [a bug](https://github.com/mikeqfu/pyhelpers/commit/e6b0a13481bb53a63a5b3884830889ce5adb611c) in the class method [PostgreSQL.import_data](https://github.com/mikeqfu/pyhelpers/blob/e6b0a13481bb53a63a5b3884830889ce5adb611c/pyhelpers/sql.py#L1106) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/e6b0a13481bb53a63a5b3884830889ce5adb611c/pyhelpers/sql.py)
- modified docstrings in the following two functions: 
  - [find_closest_point](https://github.com/mikeqfu/pyhelpers/commit/f6486366c8f0791fe6c92fb45684b8a7e87a3594) in the module [geom](https://github.com/mikeqfu/pyhelpers/blob/f6486366c8f0791fe6c92fb45684b8a7e87a3594/pyhelpers/geom.py)
  - [find_similar_str](https://github.com/mikeqfu/pyhelpers/commit/b38273fa3d991646f5a4dc0d951bed05bfee7f9d) in the module [text](https://github.com/mikeqfu/pyhelpers/blob/b38273fa3d991646f5a4dc0d951bed05bfee7f9d/pyhelpers/text.py)

**For more information about the update and/or a full walk-through of this release, check out [PyHelpers 1.2.11 documentation](https://pyhelpers.readthedocs.io/en/1.2.11/).** 



#### [1.2.10](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.10)

*1 February 2021*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.9...1.2.10) since [1.2.9](https://pypi.org/project/pyhelpers/1.2.9/):

- added the following three new functions to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/ops.py): 
  - [eval_dtype](https://github.com/mikeqfu/pyhelpers/commit/3e81a060b6ff967a93a47934f023a73b1e5ff79a#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR116)
  - [swap_cols](https://github.com/mikeqfu/pyhelpers/commit/8112735f33491ff91dfa5dc0564bda1f16e92b93#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR593)
  - [swap_rows](https://github.com/mikeqfu/pyhelpers/commit/8112735f33491ff91dfa5dc0564bda1f16e92b93#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR635)
- added a new function [get_rectangle_centroid](https://github.com/mikeqfu/pyhelpers/commit/bf248d6e1352f5d83e009d68189926bf6cfc4a03) to the module [geom](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/geom.py)
- added two new methods to the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/958942476652ca6202180ad6fd9c5eb8dfd72f22/pyhelpers/sql.py#L54) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/sql.py):
  - [.list_table_names](https://github.com/mikeqfu/pyhelpers/commit/958942476652ca6202180ad6fd9c5eb8dfd72f22#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaR936)
  - [.alter_table_schema](https://github.com/mikeqfu/pyhelpers/commit/958942476652ca6202180ad6fd9c5eb8dfd72f22#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaR995)
- made modifications (with bug fixes) to:
  - the function [np_preferences](https://github.com/mikeqfu/pyhelpers/commit/ca9ba36da9671593adb752f2301debcf03beb99c#diff-8e1ccefca5009c849b1e96129b63e9dc483acfa1049605b6872c49e549d71793R15) in the module [settings](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/settings.py)
  - the function [save_multiple_spreadsheets](https://github.com/mikeqfu/pyhelpers/commit/b96306545986a1c2763afb1aadcaf867695537b9#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R311) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/store.py)
  - the class method [PostgreSQL.read_sql_query](https://github.com/mikeqfu/pyhelpers/commit/5a8f251b570f0877d117251ec3e3408dba648398) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/9b858f42e2fca0770589ad6fb93a981b432d20a5/pyhelpers/sql.py)

**For more information about the update and/or a full walk-through of this release, check out [PyHelpers 1.2.10 documentation](https://pyhelpers.readthedocs.io/en/1.2.10/).** 



#### [1.2.9](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.9)

*5 January 2021*

*(Note that **~~1.2.8~~** had been permanently deleted.)*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.7...1.2.9) since [1.2.7](https://pypi.org/project/pyhelpers/1.2.7/):

- added a new function [get_obj_attr](https://github.com/mikeqfu/pyhelpers/commit/9f10906069fbbb20261d1ea53685d2938c689fc6) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/ops.py)
- added a new function [get_db_address](https://github.com/mikeqfu/pyhelpers/commit/7215f14c0ff284cb86a29d001b2b72bec995fa83) to the module [sql](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/sql.py)
- made modifications (with bug fixes) to:
  - the function [validate_input_data_dir](https://github.com/mikeqfu/pyhelpers/commit/f81c92d613a44272b61ee0d8fee085628e2e0880) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/dir.py)
  - the functions [confirmed](https://github.com/mikeqfu/pyhelpers/commit/eb1fa9b79a3c696c29fb0b5457fbc135cb49503e#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR23) and [fake_requests_headers](https://github.com/mikeqfu/pyhelpers/commit/ce1caaef6bf306a5a0e4014f38ed1c0a159ff529#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR887) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/ops.py)
  - the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/f43192408c548ad3d60df196d36dd970f022f954/pyhelpers/sql.py#L54) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/6dd51bfd46e08852ff38446ef0aab97351db2420/pyhelpers/sql.py)



#### [1.2.7](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.7)

*17 November 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.6...1.2.7) since [1.2.6](https://pypi.org/project/pyhelpers/1.2.6/):

- fixed [a minor bug](https://github.com/mikeqfu/pyhelpers/commit/c67a660f811d9ec370b45b9782fb7cb34d2e34c0) with [PostgreSQL.import_data](https://github.com/mikeqfu/pyhelpers/blob/c67a660f811d9ec370b45b9782fb7cb34d2e34c0/pyhelpers/sql.py#L845) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/cd74ab1de677a40fb903947ff79aa99457a69f0b/pyhelpers/sql.py)
- added the following three new functions to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/cd74ab1de677a40fb903947ff79aa99457a69f0b/pyhelpers/ops.py):
  - [merge_dicts](https://github.com/mikeqfu/pyhelpers/commit/14c639d1f956102e8f8f00017a5f4b52626ce5ba#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR324)
  - [is_network_connected](https://github.com/mikeqfu/pyhelpers/commit/14c639d1f956102e8f8f00017a5f4b52626ce5ba#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR770)
  - [is_url_connectable](https://github.com/mikeqfu/pyhelpers/commit/14c639d1f956102e8f8f00017a5f4b52626ce5ba#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR790) 
- added the following two new functions to the module [text](https://github.com/mikeqfu/pyhelpers/blob/cd74ab1de677a40fb903947ff79aa99457a69f0b/pyhelpers/text.py):
  - [get_acronym](https://github.com/mikeqfu/pyhelpers/commit/246e6a1e73c8d072f9f6c2120e92e11406263b40#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R61)
  - [extract_words1upper](https://github.com/mikeqfu/pyhelpers/commit/246e6a1e73c8d072f9f6c2120e92e11406263b40#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R107)



#### [1.2.6](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.6)

*6 November 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.5...1.2.6) since [1.2.5](https://pypi.org/project/pyhelpers/1.2.5/):

- enabled direct access to all functions/classes from importing the package (without having to specifying the modules they reside in)
- fixed [a minor bug](https://github.com/mikeqfu/pyhelpers/commit/0db725542cef75889889b1e401f0db8eaf07188d) in the function [fake_requests_headers](https://github.com/mikeqfu/pyhelpers/blob/0db725542cef75889889b1e401f0db8eaf07188d/pyhelpers/ops.py#L739) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/0db725542cef75889889b1e401f0db8eaf07188d/pyhelpers/ops.py)
- modified printing message of the method [PostgreSQL.drop_table](https://github.com/mikeqfu/pyhelpers/commit/8110b34a4bb12921bf6964199f88edc7a2c78ba1) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/8110b34a4bb12921bf6964199f88edc7a2c78ba1/pyhelpers/sql.py)
- renamed the following two functions in the module [geom](https://github.com/mikeqfu/pyhelpers/blob/ba2370b8511a06763076033546a24dd60ec23927/pyhelpers/geom.py):
  - [~~find_closest_point_from~~](https://github.com/mikeqfu/pyhelpers/commit/ba2370b8511a06763076033546a24dd60ec23927#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8L730) to [find_closest_point](https://github.com/mikeqfu/pyhelpers/blob/ba2370b8511a06763076033546a24dd60ec23927/pyhelpers/geom.py#L550)
  - [~~find_closest_points_between~~](https://github.com/mikeqfu/pyhelpers/commit/ba2370b8511a06763076033546a24dd60ec23927#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8L793) to [find_closest_points](https://github.com/mikeqfu/pyhelpers/blob/ba2370b8511a06763076033546a24dd60ec23927/pyhelpers/geom.py#L613)
- reduced the number of essential dependencies for installing the package as some import statements were put into the functions that use them (see also the [note](https://pyhelpers.readthedocs.io/en/latest/installation.html) for installation)



#### [1.2.5](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.5)

*12 October 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.4...1.2.5) since [1.2.4](https://pypi.org/project/pyhelpers/1.2.4/):

- renamed the function [~~rm_dir~~](https://github.com/mikeqfu/pyhelpers/commit/833da11ac0cc6920d85c92c6e1401ea37af96bf1#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09L206) to [delete_dir](https://github.com/mikeqfu/pyhelpers/blob/833da11ac0cc6920d85c92c6e1401ea37af96bf1/pyhelpers/dir.py#L212) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/833da11ac0cc6920d85c92c6e1401ea37af96bf1/pyhelpers/dir.py)
- moved the function [save_web_page_as_pdf](https://github.com/mikeqfu/pyhelpers/commit/95d8a9502d19868fdaa747fd7662f0832b41ca7b#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127L417) from the module [text](https://github.com/mikeqfu/pyhelpers/blob/95d8a9502d19868fdaa747fd7662f0832b41ca7b/pyhelpers/text.py) to [store](https://github.com/mikeqfu/pyhelpers/blob/b33f1df08991264622dd20876d572851a8b7e5ec/pyhelpers/store.py#L691)
- modified the function [save](https://github.com/mikeqfu/pyhelpers/commit/b33f1df08991264622dd20876d572851a8b7e5ec#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R102) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/b33f1df08991264622dd20876d572851a8b7e5ec/pyhelpers/store.py)
- removed the functions [~~get_variable_name~~](https://github.com/mikeqfu/pyhelpers/commit/c7e22ae0d2e20c9ab84e5224b300e0a660ccb2e0#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL165) and [~~get_variable_names~~](https://github.com/mikeqfu/pyhelpers/commit/c7e22ae0d2e20c9ab84e5224b300e0a660ccb2e0#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL203) from the module [ops](https://github.com/mikeqfu/pyhelpers/blob/c7e22ae0d2e20c9ab84e5224b300e0a660ccb2e0/pyhelpers/ops.py)
- modified the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/116c7c1872fc8916856ae067e1edc89f8f8580bd/pyhelpers/sql.py#L21) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/116c7c1872fc8916856ae067e1edc89f8f8580bd/pyhelpers/sql.py) with [bug fixes](https://github.com/mikeqfu/pyhelpers/commit/116c7c1872fc8916856ae067e1edc89f8f8580bd)



#### [1.2.4](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.4)

*7 September 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.3...1.2.4) since [1.2.3](https://pypi.org/project/pyhelpers/1.2.3/):

- modified the function [fake_requests_headers](https://github.com/mikeqfu/pyhelpers/commit/0462c6bb3e3d32d6266ce2a713d99c90f8b5a0c6) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/ef9caca1e696f699633a4ee619e57c9f27ae6ce2/pyhelpers/ops.py)
- made [a minor change](https://github.com/mikeqfu/pyhelpers/commit/ef4149590136a9e665e66f38f5decf64d6ccdb2c) to the installation requirements



#### [1.2.3](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.3)

*7 September 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.2...1.2.3) since [1.2.2](https://pypi.org/project/pyhelpers/1.2.2/):

- fixed [a bug](https://github.com/mikeqfu/pyhelpers/commit/76f2f097cf2bad365f84bf9fa9ba8c97454fe7ee) in the function [download_file_from_url](https://github.com/mikeqfu/pyhelpers/blob/d3e84b9af834d118d555ae0e41fb32ffa7355b9f/pyhelpers/ops.py#L36) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/d3e84b9af834d118d555ae0e41fb32ffa7355b9f/pyhelpers/ops.py)
- added a new function [fake_requests_headers](https://github.com/mikeqfu/pyhelpers/blob/0257ca607d80fccfd291e93f0f311cb73b21f1d1/pyhelpers/ops.py#L19) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/e3f8ba9ffb775d030bde7aa18df131cf6e45b5b2/pyhelpers/ops.py)
- fixed [a bug](https://github.com/mikeqfu/pyhelpers/commit/e24a68f2ec80ef6316e1b0af4c68f779225ab2d8#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L62) in the function [get_specific_filepath_info](https://github.com/mikeqfu/pyhelpers/blob/e24a68f2ec80ef6316e1b0af4c68f779225ab2d8/pyhelpers/store.py#L16) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/e3f8ba9ffb775d030bde7aa18df131cf6e45b5b2/pyhelpers/store.py)
- fixed [a few bugs](https://github.com/mikeqfu/pyhelpers/commit/319fe94aac4f215b58620b23a7556489716b59fe) in the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/commit/319fe94aac4f215b58620b23a7556489716b59fe#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaR19) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/e3f8ba9ffb775d030bde7aa18df131cf6e45b5b2/pyhelpers/sql.py)



#### [1.2.2](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.2)

*18 July 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.2.1...1.2.2) since [1.2.1](https://pypi.org/project/pyhelpers/1.2.1/):

- modified the function [get_specific_filepath_info](https://github.com/mikeqfu/pyhelpers/blob/305d08a8e7bd9aa28698360cde6ca5120d8af2aa/pyhelpers/store.py#L16) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/33002edab79a3fc976b7ae7ded2f33547dc0e5f5/pyhelpers/store.py)
- modified the following two functions in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/33002edab79a3fc976b7ae7ded2f33547dc0e5f5/pyhelpers/ops.py):
  - [split_list](https://github.com/mikeqfu/pyhelpers/commit/aa387606d2bc02834933e94a7cbccbc1e545dafe#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL222)
  - [get_all_values_from_nested_dict](https://github.com/mikeqfu/pyhelpers/commit/aa387606d2bc02834933e94a7cbccbc1e545dafe#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL341)



#### [1.2.1](https://github.com/mikeqfu/pyhelpers/releases/tag/1.2.1)

*1 July 2020*

*(Note that **~~1.2.0~~** had been permanently deleted.)*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.1.2...1.2.1) since [1.1.2](https://pypi.org/project/pyhelpers/1.1.2/):

- integrated the module [~~download~~](https://github.com/mikeqfu/pyhelpers/commit/d36527279cad92941c92eaec38b5c4ba33119f19) into [ops](https://github.com/mikeqfu/pyhelpers/blob/4a3a0c9ac83440007136f504e44562ec75b973df/pyhelpers/ops.py); and made the following changes in the module:
  - renamed the function [~~download~~](https://github.com/mikeqfu/pyhelpers/commit/d36527279cad92941c92eaec38b5c4ba33119f19#diff-6f8fcaf7c0adfbc7a2f9590aa4d76d65bbe0f8f0b383509db21cf9f01a579155L9) to [download_file_from_url](https://github.com/mikeqfu/pyhelpers/commit/0f6fb049e224398ae126ca2bf03cfeced8707480#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR18) 
  - added a new function [convert_md_to_rst](https://github.com/mikeqfu/pyhelpers/commit/82bf68e64e864efb95c728a894276367047c79fb#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R370)
  - made minor modifications to the following six functions: 
    - [split_list_by_size](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL92)
    - [split_list](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL111)
    - [get_extreme_outlier_bounds](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL246)
    - [interquartile_range](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL268)
    - [find_closest_date](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL284)
    - [detect_nan_for_str_column](https://github.com/mikeqfu/pyhelpers/commit/f262c4904d2fa305cb707e8e7fab58962924c83d#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL392)
- modified the following five functions in the module [store](https://github.com/mikeqfu/pyhelpers/blob/4a3a0c9ac83440007136f504e44562ec75b973df/pyhelpers/store.py): 
  - [get_specific_filepath_info](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L17)
  - [save_fig](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L423)
  - [save_svg_as_emf](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L469)
  - [seven_zip](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L626)
  - [load_csr_matrix](https://github.com/mikeqfu/pyhelpers/commit/fc4f4b4e00237fbb7648f96015af5c0ad34d490a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L626) 
- moved the function [save_web_page_as_pdf](https://github.com/mikeqfu/pyhelpers/commit/82bf68e64e864efb95c728a894276367047c79fb#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R304) from the module [store](https://github.com/mikeqfu/pyhelpers/blob/fc4f4b4e00237fbb7648f96015af5c0ad34d490a/pyhelpers/store.py) to [text](https://github.com/mikeqfu/pyhelpers/blob/82bf68e64e864efb95c728a894276367047c79fb/pyhelpers/text.py)
- modified the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/commit/4598e3e16d706f1cc4472d774ecd4dbf53d4eb28#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaL20) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/4a3a0c9ac83440007136f504e44562ec75b973df/pyhelpers/sql.py)
- created [PyHelpers documentation](https://readthedocs.org/projects/pyhelpers/) hosted at [Read the Docs](https://readthedocs.org/)



#### [1.1.2](https://github.com/mikeqfu/pyhelpers/releases/tag/1.1.2)

*30 May 2020*

*(Note that **~~1.1.1~~** had been permanently deleted.)*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.1.0...1.1.2) since [1.1.0](https://pypi.org/project/pyhelpers/1.1.0/):

- added a new function [sketch_square](https://github.com/mikeqfu/pyhelpers/commit/3e412e536ead2346221b82cb2018f0577fdf03c0#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R681-R735) to the module [geom](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/geom.py)
- added the following two new functions to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/ops.py)
  - [create_rotation_matrix](https://github.com/mikeqfu/pyhelpers/commit/ff069a10f9f61c33ed43520a2b7bf20bd3c262ea#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR413-R425)
  - [dict_to_dataframe](https://github.com/mikeqfu/pyhelpers/commit/3444c80cbb05789d623233206b1ebbf528227730#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR429-R439)
- added the following five new functions to the module [store](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/store.py):
  - [save_multiple_spreadsheets](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R268-R342)
  - [load_multiple_spreadsheets](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R345-R388)
  - [unzip](https://github.com/mikeqfu/pyhelpers/commit/df7614ad9d96b526394a4914d69bc6c3dfa34679#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R560-R589)
  - [seven_zip](https://github.com/mikeqfu/pyhelpers/commit/df7614ad9d96b526394a4914d69bc6c3dfa34679#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R592-R623)
  - [load_csr_matrix](https://github.com/mikeqfu/pyhelpers/commit/df7614ad9d96b526394a4914d69bc6c3dfa34679#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R626-R649)
- added the following six new functions to the module [text](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/text.py):
  - [remove_punctuation](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R60-R78)
  - [count_words](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R81-R96)
  - [calculate_idf](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R99-R122)
  - [calculate_tf_idf](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R125-R138)
  - [euclidean_distance_between_texts](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R141-R168)
  - [cosine_similarity_between_texts](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R171-R208)
- renamed the following function/method:
  - the function [~~save_excel~~](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607L114-L115) to [save_spreadsheet](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R220-R265) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/store.py)
  - the method [~~.disconnect~~](https://github.com/mikeqfu/pyhelpers/commit/ad67be119ee4f74b04803a7d73cbeafb74bbc63b#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaL124) to [.disconnect_database](https://github.com/mikeqfu/pyhelpers/commit/ad67be119ee4f74b04803a7d73cbeafb74bbc63b#diff-c615ea7745f60e95fd1c84af5ceaa8453c550332f69ad7fa84a50053bdb91dbaR126) of the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/sql.py#L20) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/sql.py)
- removed the parameter `encoding` from relevant functions in the module [store](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/store.py)
- removed the function [~~csr_matrix_to_dict~~](https://github.com/mikeqfu/pyhelpers/commit/40d7a3234690dfdba26294c814bcee41b8c15acf#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127L50-L58) from the module [text](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/text.py)
- added an optional parameter `**kwargs` to the following functions:
  - [cd](https://github.com/mikeqfu/pyhelpers/commit/780b8bf50db0a265084ffcff91479c7d5c12bb4d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R11), [cdd](https://github.com/mikeqfu/pyhelpers/commit/780b8bf50db0a265084ffcff91479c7d5c12bb4d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R32), [cd_dat](https://github.com/mikeqfu/pyhelpers/commit/780b8bf50db0a265084ffcff91479c7d5c12bb4d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R56) and [rm_dir](https://github.com/mikeqfu/pyhelpers/commit/780b8bf50db0a265084ffcff91479c7d5c12bb4d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R125) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/dir.py)
  - [download](https://github.com/mikeqfu/pyhelpers/commit/860cfd69ddf26480af722f59018550c83763b091#diff-6f8fcaf7c0adfbc7a2f9590aa4d76d65bbe0f8f0b383509db21cf9f01a579155R10) in the module [download](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/download.py):
  - [save_svg_as_emf](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R467) and [save_web_page_as_pdf](https://github.com/mikeqfu/pyhelpers/commit/646bcccdd2b01f70ecbac939d00c37c855fde92a#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R501-R502) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/7b6a647bc7d672c604306bb335b783663b6d0b9d/pyhelpers/store.py)



#### [1.1.0](https://github.com/mikeqfu/pyhelpers/releases/tag/1.1.0)

*22 April 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.26...1.1.0) since [1.0.26](https://pypi.org/project/pyhelpers/1.0.26/):

- made [a few modifications](https://github.com/mikeqfu/pyhelpers/commit/eac4bc4a2a4665017f18452a89cbacf4fdecd6d7) to the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/blob/2326cd2e11e8264bc96a71386755206123b554d1/pyhelpers/sql.py#L20) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/2326cd2e11e8264bc96a71386755206123b554d1/pyhelpers/sql.py) to speed up importing data into and retrieving data from a PostgreSQL database
- modified the two modules [store](https://github.com/mikeqfu/pyhelpers/commit/79a2a01ce07c813a170643e2ba19c51a8e5c66e6) and [text](https://github.com/mikeqfu/pyhelpers/commit/de0cd35ead0224a7decda8527edb8bea816dd2a1)
- fixed [a minor bug](https://github.com/mikeqfu/pyhelpers/commit/de0cd35ead0224a7decda8527edb8bea816dd2a1#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127L42) in the function [find_matched_str](https://github.com/mikeqfu/pyhelpers/blob/2326cd2e11e8264bc96a71386755206123b554d1/pyhelpers/text.py#L34) in the module [text](https://github.com/mikeqfu/pyhelpers/blob/2326cd2e11e8264bc96a71386755206123b554d1/pyhelpers/text.py)



#### [1.0.26](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.26)

*12 March 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.25...1.0.26) since [1.0.25](https://pypi.org/project/pyhelpers/1.0.25/):

- fixed [a few bugs](https://github.com/mikeqfu/pyhelpers/commit/96ffbafcdd27f245c3462c009f3cb66111f61ffa) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/6fe6c272bdb6042ec6040c6164d0d9b9554faf11/pyhelpers/store.py)



#### [1.0.25](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.25)

*6 March 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.24...1.0.25) since [1.0.24](https://pypi.org/project/pyhelpers/1.0.24/):

- upgraded from *pyproj 1* to *pyproj 2* for two functions: [osgb36_to_wgs84](https://github.com/mikeqfu/pyhelpers/commit/d8f6a36b2a6e1ec54ec0ec4faa637337f7542bd1#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R21-R25) and [wgs84_to_osgb36](https://github.com/mikeqfu/pyhelpers/commit/d8f6a36b2a6e1ec54ec0ec4faa637337f7542bd1#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R42-R46), in the module [geom](https://github.com/mikeqfu/pyhelpers/blob/3f0baeae6c63f3afb8ea8cf1cdff35c9647c92f0/pyhelpers/geom.py) 



#### [1.0.24](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.24)

*28 January 2020*

*(Note that **~~1.0.23~~** had been permanently deleted.)*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.22...1.0.24) since [1.0.22](https://pypi.org/project/pyhelpers/1.0.22/):

- fixed [a bug](https://github.com/mikeqfu/pyhelpers/commit/039c09ebaa879d5251ba967824bd12c317ed9206) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/383b226e0e27fb6622f405a62a016601bc844666/pyhelpers/sql.py)



#### [1.0.22](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.22)

*27 January 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.21...1.0.22) since [1.0.21](https://pypi.org/project/pyhelpers/1.0.21/):

- added two new functions to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/ops.py):
  - [split_list](https://github.com/mikeqfu/pyhelpers/commit/afa60ee31793f619ee3979704ffc6709543241c8#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR107-R122)
  - [split_iterable](https://github.com/mikeqfu/pyhelpers/commit/afa60ee31793f619ee3979704ffc6709543241c8#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR125-R142)
- renamed the function [~~divide_list_into_chunks~~](https://github.com/mikeqfu/pyhelpers/commit/afa60ee31793f619ee3979704ffc6709543241c8#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aL88) to [split_list_by_size](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/ops.py#L90) in the module [ops](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/ops.py)
- made modifications to:
  - the function [gdal_configurations](https://github.com/mikeqfu/pyhelpers/commit/0d8a461b89f0d8a917e52a491c17e8f6d0cbf3cf) in the module [settings](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/settings.py)
  - the class [PostgreSQL](https://github.com/mikeqfu/pyhelpers/commit/dfeaf212bbaa3ee05dd60d7fe9f6f33cc58e0ced) in the module [sql](https://github.com/mikeqfu/pyhelpers/blob/9826ef52afc1018c9e17b518de6ea5ebec7edc88/pyhelpers/sql.py)



#### [1.0.21](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.21)

*20 January 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.20...1.0.21) since [1.0.20](https://pypi.org/project/pyhelpers/1.0.20/):

- added a new module [sql](https://github.com/mikeqfu/pyhelpers/blob/8f86efcee944b172eb9c525077b3b2425e5730ae/pyhelpers/sql.py)
- added a new function [detect_nan_for_str_column](https://github.com/mikeqfu/pyhelpers/commit/0c02a011193e36619c4ee1828fd15bd501b58025#diff-9266f224c0227114f50836ba656288a96bd7cca831301fe025c5a7cf9f4ab45aR320-R328) to the module [ops](https://github.com/mikeqfu/pyhelpers/blob/8f86efcee944b172eb9c525077b3b2425e5730ae/pyhelpers/ops.py)



#### [1.0.20](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.20)

*7 January 2020*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.19...1.0.20) since [1.0.19](https://pypi.org/project/pyhelpers/1.0.19/):

- fixed [a few minor bugs](https://github.com/mikeqfu/pyhelpers/commit/8ce0aa9bd7c285b1b936ae54fe6d51d386bdbf77) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/425184670493a3f5e4bf65fac1aac5232071f18b/pyhelpers/store.py)



#### [1.0.19](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.19)

*28 November 2019*

*(Note that **~~1.0.18~~** had been permanently deleted.)*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.17...1.0.19) since [1.0.17](https://pypi.org/project/pyhelpers/1.0.17/):

- added three new functions to the module [geom](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/geom.py):
  - [show_square](https://github.com/mikeqfu/pyhelpers/commit/8abec1f3c522409fe72b4075b4a0188b261a5661#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R363-R384)
  - [locate_square_vertices](https://github.com/mikeqfu/pyhelpers/commit/8abec1f3c522409fe72b4075b4a0188b261a5661#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R387-R429)
  - [locate_square_vertices_calc](https://github.com/mikeqfu/pyhelpers/commit/8abec1f3c522409fe72b4075b4a0188b261a5661#diff-dc4a0e4af0eb0e5a833d868a38bde78a7c5736be4021d9ddf03b97c6f0cc8af8R432-R472)
- added a new function [is_dirname](https://github.com/mikeqfu/pyhelpers/commit/db7303b4dd4b92281f53c6a8a107efedeafb557d#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R75-R95) to the module [dir](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/dir.py)
- added a parameter `encoding` to five functions in the module [store](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/store.py):
  - [save_pickle](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R66)
  - [load_pickle](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R96)
  - [save_json](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R113)
  - [load_json](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R142)
  - [save](https://github.com/mikeqfu/pyhelpers/commit/aedd7f2d33dfa72fdcd6cc23922982125509e0eb#diff-5be4770b2702d34ea60ff69d076c06b6311d2de302323f4313f5829f857e7607R204)
- renamed the module [~~misc~~](https://github.com/mikeqfu/pyhelpers/commit/65c0e41844989c5fecd0d114315002752ac1ce3c) to [ops](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/ops.py); moved the function [csr_matrix_to_dict](https://github.com/mikeqfu/pyhelpers/commit/ad191ddacac3344182a875ebd13b7c36526d2eb9#diff-07b6d8c6102940f884435a3670eb5007494d5c51b4deb718ba79c3b267825127R50-R63) from [ops](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/ops.py) to [text](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/text.py); 
- fixed minor bugs in the following functions:
  - [save_feather](https://github.com/mikeqfu/pyhelpers/commit/78b446f0152a098553dc8b9c3c68ce0f655362e0) and [load_feather](https://github.com/mikeqfu/pyhelpers/commit/151ca2f436363091b77a8b8cc1284e6956c7db97) in the module [store](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/store.py)
  - [download](https://github.com/mikeqfu/pyhelpers/commit/937908d2953cbed4848a400d5f2530d4dfb02456) in the module [download](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/download.py)
  - [mpl_preferences](https://github.com/mikeqfu/pyhelpers/commit/73c7b66685a64147c998c03bd003d1f8d8c42eb3) in the module [settings](https://github.com/mikeqfu/pyhelpers/blob/1bf9df9a354ee14d8c112afdd08805eae5de5e1b/pyhelpers/settings.py)



#### [1.0.17](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.17)

*10 September 2019*

##### Main [changes](https://github.com/mikeqfu/pyhelpers/compare/1.0.16...1.0.17) since [1.0.16](https://pypi.org/project/pyhelpers/1.0.16/):

- modified the function [rm_dir](https://github.com/mikeqfu/pyhelpers/commit/f3b4e1bb9654c2102bea524cb280c19030f80163#diff-9658546df62eded721ef6049c33f4b2d7e985d9cce8c08ba9538a32da5229a09R100-R121) in the module [dir](https://github.com/mikeqfu/pyhelpers/blob/3961ec9a2a2c15d60454551d758b20875cd02570/pyhelpers/dir.py)
- tidied up the code of three modules: 
  - [misc](https://github.com/mikeqfu/pyhelpers/commit/ffa1220c443e5d26587d6469104e5dde05d8e4e4)
  - [geom](https://github.com/mikeqfu/pyhelpers/commit/d8a9b0defd7a4539a89b150250e26a2967924f9b)
  - [store](https://github.com/mikeqfu/pyhelpers/commit/36809752328e1bfe9a30bf67fd2e36c6f332009d)



#### [1.0.16](https://github.com/mikeqfu/pyhelpers/releases/tag/1.0.16)

*3 September 2019*

**A brand-new release.**

The initial release and the early versions up to ***~~1.0.15~~*** had been permanently deleted.
