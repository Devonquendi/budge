/**
 * Every call the browser app makes to FastAPI. Pages import this; components
 * never do.
 *
 * In dev, Vite proxies /api to :8000; in production vercel.json rewrites it to
 * the api service. Either way it's the same origin, so the session cookie rides
 * along without any CORS setup.
 */

export type Account = {
  id: string
  name: string
  type: string
  connection_name: string
  formatted_account: string | null
  currency: string
  /** A decimal string, not a number — see money.ts. */
  balance_current: string
  balance_available: string | null
}

export type Me = {
  email: string
  /** False until Akahu tokens are stored, which gates every account endpoint. */
  onboarded: boolean
}

export type Connection = { connected: boolean }

export type Selection = {
  accounts: Account[]
  included: string[]
}

/** Thrown for any non-2xx response, carrying FastAPI's `detail` as the message. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message)
  }
}

/** FastAPI sends a string for our own errors and a list for validation ones. */
function detailMessage(body: unknown, fallback: string): string {
  if (typeof body !== 'object' || body === null) return fallback
  const { detail } = body as { detail?: unknown }
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && typeof detail[0]?.msg === 'string') return detail[0].msg
  return fallback
}

async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method,
    headers: body === undefined ? undefined : { 'content-type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    const fallback = `Request failed (${response.status})`
    throw new ApiError(response.status, detailMessage(payload, fallback))
  }

  return response.status === 204 ? (undefined as T) : response.json()
}

export const api = {
  /** Null rather than throwing on 401: "not signed in" is a normal answer here. */
  async me(): Promise<Me | null> {
    try {
      return await request<Me>('/auth/me')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) return null
      throw error
    }
  },

  login: (email: string, password: string) =>
    request<Me>('/auth/login', 'POST', { email, password }),

  signup: (email: string, password: string, invite_code: string) =>
    request<Me>('/auth/signup', 'POST', { email, password, invite_code }),

  logout: () => request<void>('/auth/logout', 'POST'),

  connection: () => request<Connection>('/akahu'),

  connect: (app_token: string, user_token: string) =>
    request<Connection>('/akahu', 'PUT', { app_token, user_token }),

  accounts: () => request<Account[]>('/accounts'),

  selection: () => request<Selection>('/accounts/selection'),

  saveSelection: (included: string[]) =>
    request<Selection>('/accounts/selection', 'PUT', { included }),
}

/** The message to put in front of the user when a call fails. */
export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong'
}
