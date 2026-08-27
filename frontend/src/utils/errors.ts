/**
 * The message from a caught value.
 *
 * `catch (err)` binds `unknown` under `useUnknownInCatchVariables`, and every
 * page wants the same thing from it: something printable.
 */
export function errorMessage(err: unknown, fallback = 'An unexpected error occurred'): string {
  if (err instanceof Error) return err.message || fallback;
  if (typeof err === 'string' && err) return err;
  return fallback;
}
