/**
 * Links from API Explorer pages must stay on the explored API, and links from
 * this site's own pages must not pick one up.
 *
 * Run with: npm test
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  apiQuery,
  attributePath,
  collectionPath,
  transientAttributes,
} from '../src/utils/explorerLinks.ts';

const API = 'https://seqcolapi-demo.databio.org';
const Q = `?url=${encodeURIComponent(API)}`;

test('no explored API means no ?url=', () => {
  assert.equal(apiQuery(null), '');
  assert.equal(attributePath('names', 'abc', null), '/attribute/names/abc');
  assert.equal(collectionPath('xyz', null), '/collection/xyz');
});

test('an explored API rides along as ?url=', () => {
  assert.equal(apiQuery(API), Q);
  assert.equal(attributePath('names', 'abc', API), `/attribute/names/abc${Q}`);
  assert.equal(collectionPath('xyz', API), `/explore-api/collection/xyz${Q}`);
});

test('transient attributes come from the published schema', () => {
  const info = (ga4gh: unknown) => ({ seqcol: { schema: { properties: {}, ga4gh } } });
  assert.deepEqual(transientAttributes(info({ transient: ['a', 'b'] })), ['a', 'b']);
  assert.deepEqual(transientAttributes(info({})), []);
});

test('without a schema, fall back to the spec default', () => {
  assert.deepEqual(transientAttributes(null), ['sorted_name_length_pairs']);
  assert.deepEqual(transientAttributes({ seqcol: { schema: null } }), ['sorted_name_length_pairs']);
});
