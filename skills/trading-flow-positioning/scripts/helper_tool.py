#!/usr/bin/env python3
"""Check supplied JSON against this package schema; structural only."""
import argparse,json,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument('--kind',choices=['input','output'],required=True);p.add_argument('--file',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[1]; repo=root.parents[1];sys.path.insert(0,str(repo/'packages/contracts'))
 from linkskills_contracts.validate import validate_instance
 schema=json.loads((root/'references/schemas.json').read_text())['definitions'][a.kind];obj=json.loads(a.file.read_text());res=validate_instance(obj,schema)
 if res.ok: print(json.dumps({'status':'STRUCTURE_VALID','method_qualified':False}));return 0
 print(json.dumps({'status':'STRUCTURE_INVALID','errors':[str(e) for e in res.errors],'method_qualified':False}));return 1
if __name__=='__main__':raise SystemExit(main())
