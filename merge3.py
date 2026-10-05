"""Line-based three-way merge (the same idea as `diff3` / git merge).

merge(base, ours, theirs) combines two edited versions of `base`:
  * ours   = the page as it is on the wiki now (may contain hand edits)
  * theirs = the page freshly generated from the docs
Changes made on only one side are taken; regions changed differently on both sides are conflicts.
"""
from difflib import SequenceMatcher


def _blocks(a, b):
    return [m for m in SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks() if m.size]


def _sync_regions(base, a, b):
    am, bm = _blocks(base, a), _blocks(base, b)
    ia = ib = 0
    out = []
    while ia < len(am) and ib < len(bm):
        abase, amatch, alen = am[ia]
        bbase, bmatch, blen = bm[ib]
        lo, hi = max(abase, bbase), min(abase + alen, bbase + blen)
        if lo < hi:
            asub = amatch + (lo - abase)
            bsub = bmatch + (lo - bbase)
            out.append((lo, hi, asub, asub + hi - lo, bsub, bsub + hi - lo))
        if abase + alen < bbase + blen:
            ia += 1
        else:
            ib += 1
    out.append((len(base), len(base), len(a), len(a), len(b), len(b)))
    return out


def merge(base, ours, theirs):
    """Return (merged_text, conflicts). conflicts is a list of (base_lines, our_lines, their_lines).
    When there are conflicts, merged_text contains git-style conflict markers."""
    B, A, T = base.splitlines(True), ours.splitlines(True), theirs.splitlines(True)
    out, conflicts = [], []
    iz = ia = ib = 0
    for zs, ze, as_, ae, bs, be in _sync_regions(B, A, T):
        a_chunk, b_chunk, z_chunk = A[ia:as_], T[ib:bs], B[iz:zs]
        if a_chunk or b_chunk:
            if a_chunk == b_chunk:
                out += a_chunk
            elif a_chunk == z_chunk:
                out += b_chunk          # only the docs changed this part
            elif b_chunk == z_chunk:
                out += a_chunk          # only the wiki (hand edit) changed this part
            elif z_chunk and a_chunk[-len(z_chunk):] == z_chunk and len(a_chunk) > len(z_chunk):
                out += a_chunk[:-len(z_chunk)] + b_chunk   # hand edit only inserted lines just before a docs change
            elif z_chunk and a_chunk[:len(z_chunk)] == z_chunk and len(a_chunk) > len(z_chunk):
                out += b_chunk + a_chunk[len(z_chunk):]    # hand edit only inserted lines just after a docs change
            elif z_chunk and b_chunk[-len(z_chunk):] == z_chunk and len(b_chunk) > len(z_chunk):
                out += b_chunk[:-len(z_chunk)] + a_chunk   # docs only inserted lines just before a hand edit
            elif z_chunk and b_chunk[:len(z_chunk)] == z_chunk and len(b_chunk) > len(z_chunk):
                out += a_chunk + b_chunk[len(z_chunk):]    # docs only inserted lines just after a hand edit
            else:
                conflicts.append((z_chunk, a_chunk, b_chunk))
                nl = lambda c: c if (not c or c[-1].endswith('\n')) else c[:-1] + [c[-1] + '\n']
                out += ['<<<<<<< wiki (hand edit)\n'] + nl(a_chunk) + ['=======\n'] + nl(b_chunk) + ['>>>>>>> docs\n']
        out += A[as_:ae]
        iz, ia, ib = ze, ae, be
    return ''.join(out), conflicts


if __name__ == '__main__':
    base = 'a\nb\nc\nd\ne\n'
    ours = 'a\nB-hand\nc\nd\ne\n'
    theirs = 'a\nb\nc\nD-docs\ne\nf\n'
    m, c = merge(base, ours, theirs)
    assert m == 'a\nB-hand\nc\nD-docs\ne\nf\n' and not c, m
    m, c = merge(base, 'a\nX\nc\nd\ne\n', 'a\nY\nc\nd\ne\n')
    assert len(c) == 1, c
    print('merge3 self-test ok')
