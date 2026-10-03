import "server-only";

/**
 * Read a setting from the server's environment at request time.
 *
 * Next freezes `NEXT_PUBLIC_` values into the build, so a value that differs
 * per environment is read here instead, and one image runs everywhere.
 */
export function requiredEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} must be set in the environment.`);
  }
  return value;
}
