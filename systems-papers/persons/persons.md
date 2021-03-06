The file `persons.csv` contains aggregated information about all authors, TPC chairs, and TPC members in the selected conference subset.
The data was generated by `src/gather_persons.py` from git hash a50c9ce


### Field description {-}

  * `name` (string): Full person name, normalized and quoted.
  * `gs_email` (string): The last current email affiliation of the author as reported by GS.
  * `as_pc_chair` (int): The number of times this person chaird a TPC.
  * `as_pc` (int): Number of times this person participated in a TPC.
  * `as_session_chair` (int): Number of times this person chaired a session.
  * `as_panelist` (int): Number of panels this person participated in or moderated.
  * `as_keynote_speaker` (int): Number of keynotes this person gave.
  * `as_author` (int): Number of papers this person (co)authored.
  * `pc_chairs` (list of strings): Conferences in which this person chaired the TPC.
  * `pcs` (list of strings): Conferences in which this person was a member of the TPC.
  * `session_chairs` (list of strings): Conferences in which this person chaired a session (with repeates).
  * `panels` (list of strings): Conferences in which this person participated in a panel (with repeates).
  * `keynotes` (list of strings): Conferences in which this person gave a keynote.
  * `papers` (list of strings): Papers this person (co)authored.
  * `gender` (categorical string): Verified or inferred gender.
  * `country` (categorical string): Two-letter country code from GS email affiliation.
  * `sector` (categorical string): Employer sector from GS email affiliation.
  * `npubs` (int): Author's total publications (minimum across all conferences).
  * `hindex` (int): Author's H-index (minimum).
  * `hindex5y` (int): Author's H-index for past 5 years (minimum).
  * `i10index` (int): Author's i10 index (minimum).
  * `i10index5y` (int): Author's i10 index for past 5 years (minimum).
  * `citedby` (int): Author's total citations (minimum).
