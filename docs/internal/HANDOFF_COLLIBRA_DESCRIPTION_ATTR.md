# Handoff — Collibra description attribute type must be configurable

> **Status (2026-08-18, dev session): implemented in 1.16.1.**
> description_attr_type_id on CollibraConfig + org config (default = OOTB Description, current behavior preserved), wired through 08; example yaml + config comment carry the discovery guidance. Discovery candidate-marker: deferred as nice-to-have.

**From:** review session, 2026-08-17 (Sunny's work deployment). **To:** dev
session.

## Finding

CollibraAdapter hardcodes DESCRIPTION_ATTR_TYPE_ID (the OOTB "Description"
attribute, ...000000003114) as a class constant. Enterprise Collibra
instances customize asset page layouts — the prominent "description" box
for a given asset type may be backed by a DIFFERENT attribute type
(custom attr, source-sync field). Sunny observed exactly this in July
testing: description written, wrong field displayed. domain_id is
unrelated (creation-path only).

## Wanted

1. `description_attr_type_id: str = "00000000-0000-0000-0000-000000003114"`
   on CollibraConfig (org_config adapters.collibra block), used by
   _set_description_attribute and update_description in place of the
   class constant. Default preserves current behavior.
2. Note in the example yaml + install guide: "if descriptions don't
   appear in the expected field, run collibra_discovery against one
   asset and set this to the attribute type your layout displays."
3. Nice-to-have: collibra_discovery prints attribute types with a
   "candidate description fields" marker (string-type attrs with
   description-like names) to make step 2 one look.
