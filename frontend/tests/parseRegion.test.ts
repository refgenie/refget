/**
 * parseRegion is the only piece of the browser extractor that can be tested
 * without a network and a wasm runtime; the byte-range read itself is verified
 * by hand against a served store.
 *
 * Run with: npm test
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { parseRegion } from '../src/utils/parseRegion.ts';

const LEN = 5000;

test('start-end', () => {
  assert.deepEqual(parseRegion('1000-2000', LEN), { start: 1000, end: 2000 });
});

test('start:end', () => {
  assert.deepEqual(parseRegion('1000:2000', LEN), { start: 1000, end: 2000 });
});

test('a bare number is one base', () => {
  assert.deepEqual(parseRegion('42', LEN), { start: 42, end: 43 });
});

test('a leading sequence name is ignored', () => {
  assert.deepEqual(parseRegion('chr20:1000-2000', LEN), { start: 1000, end: 2000 });
  assert.deepEqual(parseRegion('chr20:1000', LEN), { start: 1000, end: 1001 });
});

test('whitespace and digit grouping are ignored', () => {
  assert.deepEqual(parseRegion(' 1,000 - 2_000 ', LEN), { start: 1000, end: 2000 });
});

test('the end is clamped to the sequence length', () => {
  assert.deepEqual(parseRegion('4000-99999', LEN), { start: 4000, end: LEN });
});

test('a reversed range is rejected', () => {
  assert.throws(() => parseRegion('2000-1000', LEN), /must be greater than start/);
});

test('an empty range is rejected', () => {
  assert.throws(() => parseRegion('1000-1000', LEN), /must be greater than start/);
});

test('a start past the sequence end is rejected', () => {
  assert.throws(() => parseRegion('9000-9500', LEN), /past the end of the sequence/);
});

test('unparseable input is rejected', () => {
  assert.throws(() => parseRegion('', LEN), /Enter a region/);
  assert.throws(() => parseRegion('1000-2000-3000', LEN), /Cannot read/);
  assert.throws(() => parseRegion('chr20', LEN), /Cannot read/);
});
