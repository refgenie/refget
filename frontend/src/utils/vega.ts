import type { VisualizationSpec } from 'vega-embed';
import type { EmbedOptions } from 'vega-embed';

/**
 * Hand-written Vega-Lite specs widen their string literals (`'rect'` becomes
 * `string`), so TypeScript cannot match them against `VisualizationSpec`'s
 * discriminated unions. The objects are valid specs; this asserts that once,
 * here, rather than at every plot.
 */
export const asSpec = (spec: Record<string, unknown>): VisualizationSpec =>
  spec as unknown as VisualizationSpec;

/**
 * Same story for embed options: `config.baseURL` keeps Vega resolving gradient
 * URLs relatively, and is not in vega-lite's `Config` type.
 */
export const asEmbedOptions = (options: Record<string, unknown>): EmbedOptions =>
  options as unknown as EmbedOptions;
