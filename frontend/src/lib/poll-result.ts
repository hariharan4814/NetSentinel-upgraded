export type Result<T> = { data?: T; error?: string };

// Historical records survive a failed refresh within the mounted session/mode.
// A successful response (including an empty page) replaces the previous result.
export function retainOnError<T>(previous: Result<T>, incoming: Result<T>): Result<T> {
  return incoming.error ? { ...incoming, data: previous.data } : incoming;
}
