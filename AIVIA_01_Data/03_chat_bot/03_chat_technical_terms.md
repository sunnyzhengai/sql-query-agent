03_chat_technical_terms — the technical vocabulary of the dictionary graph

Structure: keyword | maps_to | kind | synonyms | ruled
Kinds: population (directs a term's search), operation (names what the
graph should do), property (a stored attribute of a node or edge).
This file is its own ruling registry — adding a row IS the ruling,
dated in the row (contract, Output File 1). Sunny is the only author.
The LLM segmentation prompt carries this list as data and nothing else.

| keyword     | maps_to            | kind       | synonyms                                              | ruled      |
|-------------|--------------------|------------|-------------------------------------------------------|------------|
| table       | table nodes        | population | tables, entity, master file, dataset                  | 2026-09-30 |
| column      | column nodes       | population | columns, field, fields, attribute, variable           | 2026-09-30 |
| value       | value rows         | population | values, code, codes, category, lookup, meaning of     | 2026-09-30 |
| join        | join edges         | operation  | joins, link, relate, connect, foreign key, FK, path   | 2026-09-30 |
| primary key | pk property        | property   | PK, unique key, identifier, row id                    | 2026-09-30 |
| data type   | data_type property | property   | type, datetime, varchar, numeric                      | 2026-09-30 |
| description | description texts  | property   | definition, documentation, what is                    | 2026-09-30 |
| INI         | column_ini/item    | property   | item, master file item, item number                   | 2026-09-30 |
| deprecated  | deprecated_yn      | property   | retired, obsolete                                     | 2026-09-30 |
