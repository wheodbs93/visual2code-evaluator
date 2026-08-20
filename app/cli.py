from __future__ import annotations
import argparse
import os
from .orchestrator import run_pair, run_side, demo
from .store import load_pairs
from .server import serve

def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd', required=True)
    d=sub.add_parser('demo'); d.set_defaults(fn=lambda a: demo())
    r=sub.add_parser('run-pair'); r.add_argument('--pair-id',required=True); r.add_argument('--models',default='claude,codex'); r.set_defaults(fn=lambda a: run_pair(a.pair_id, tuple(a.models.split(',',1))))
    ra=sub.add_parser('run-side'); ra.add_argument('--pair-id',required=True); ra.add_argument('--side',choices=['claude','codex'],required=True); ra.set_defaults(fn=lambda a: run_side(a.pair_id, a.side))
    s=sub.add_parser('serve'); s.add_argument('--host',default='0.0.0.0'); s.add_argument('--port',type=int,default=int(os.getenv('PORT','8080'))); s.set_defaults(fn=lambda a: serve(a.host,a.port))
    l=sub.add_parser('list-pairs'); l.set_defaults(fn=lambda a: [(p.pair_id, p.strategy, p.complexity, p.status) for p in load_pairs().values()])
    a=p.parse_args(); result=a.fn(a); 
    if result is not None: print(result.to_dict() if hasattr(result,'to_dict') else result)
if __name__=='__main__': main()
