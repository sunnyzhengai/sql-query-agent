The layers. For each file, the engine builds descriptions at different depths:

- Deep levels (statements, predicates, expressions) get technical sentences only. They're the evidence base 97 never shown to Collibra directly.\
- Scope level (each named working selection 97 your CTEs and temp tables, like ASSESSMENTS, DECLINED): gets a business term 97 the entries under "terms". Each has a proposed name (bt_name), a business_description, its technical_definition, and its own gate verdict.\
- File level: gets one business card 97 the "description" field. It also has its own gate verdict, separate from all the terms.  
  
So business voice exists at two grains 97 file and scope 97 and each one is gated independently. That's the answer to your central confusion: USP_CCHP_1 has 4 of 5 terms gate_passed, but the file's own card broke a rule, so the file-level description fell to the technical floor. One doesn't rescue the other.  
  
How to read what you pasted:  
\
- "voice": "technical", "status": "floor" on the file = the file card failed its gate after 3 tries.\
- "status": "gate_passed" on a term = that scope's business text is good and waiting for your blessing.\
- "gate_findings": ["V-3: SQL word 'procedure'"] = the exact rule it broke. V-rules you've met: V-1 = used a number with no basis in the SQL, V-3 = used a database word, V-4 = put an exclusion in the "who's in it" line.  
  
One thing ai_delivery.json doesn't show: the file card's failure reasons. Those live in the 07 sheet. This cell shows every floored file, why, and the text it wanted to publish:  
  
import json  
rows = json.load(open(  
  "/lakehouse/default/Files/out/07/07_business_sheet.json"))  
for r in rows:  
  if r["grain"] == "file" and r["status"] == "floor":  
  print("=" * 60)  
  print(r["node_id"].split("::")[-1],  
        "| tries:", r["rounds_used"])  
  for f in r["gate_findings"]:  
      print("  broke:", f)  
  print("  wanted to say:",  
        (r.get("last_proposal") or "")[:500])\

}