/**
 * Parse a region string into 0-based, half-open [start, end) coordinates.
 *
 * Accepted forms (a leading sequence name is ignored — the caller already knows
 * which sequence it is reading):
 *
 *   "1000-2000"        bases 1000 through 1999
 *   "1000:2000"        the same
 *   "chr20:1000-2000"  the same; "chr20" is dropped
 *   "1000"             the single base at 1000
 *
 * Digit grouping ("1,000", "1_000") and whitespace are ignored. A lone
 * coordinate means one base rather than "to the end of the sequence": these
 * regions are decoded in the browser, so an accidental whole-chromosome read is
 * a worse default than an obviously-too-small one.
 *
 * The end is clamped to the sequence length; a backwards or empty range is an
 * error rather than a silent no-op.
 */

export interface Region {
  start: number;
  end: number;
}

export function parseRegion(text: string, seqLength: number): Region {
  const cleaned = String(text ?? '').replace(/[\s,_]/g, '');
  if (!cleaned) throw new Error('Enter a region, for example 0-1000.');

  // Strip a leading sequence name ("chr20:..."), but not the start coordinate
  // of a "1000:2000" region — a name is anything that is not purely digits.
  const named = /^([^:]*):(.+)$/.exec(cleaned);
  const coords = named && !/^\d+$/.test(named[1]) ? named[2] : cleaned;

  const parts = coords.split(/[-:]/);
  if (parts.length > 2 || parts.some((p) => !/^\d+$/.test(p))) {
    throw new Error(`Cannot read "${text}" as a region. Try 1000-2000.`);
  }

  const start = parseInt(parts[0], 10);
  const rawEnd = parts.length === 2 ? parseInt(parts[1], 10) : start + 1;

  if (rawEnd <= start) {
    throw new Error(`Region end (${rawEnd}) must be greater than start (${start}).`);
  }
  if (start >= seqLength) {
    throw new Error(`Start ${start} is past the end of the sequence (length ${seqLength}).`);
  }

  return { start, end: Math.min(seqLength, rawEnd) };
}
