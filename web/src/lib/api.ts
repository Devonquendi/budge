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
  /** Akahu's URL for the bank's own mark, absent for some providers. */
  connection_logo: string | null
  formatted_account: string | null
  currency: string
  /** A decimal string, not a number. See money.ts. */
  balance_current: string
  balance_available: string | null
  /** What the user renamed this account to. Null means the bank's name stands. */
  nickname: string | null
}

export type Me = {
  email: string
  /** What the user asked to be called, or null if they never said. */
  name: string | null
  /** False until Akahu tokens are stored, which gates every account endpoint. */
  onboarded: boolean
}

export type Connection = { connected: boolean }

export type Category = {
  name: string
  id: string | null
  /** The broad NZFCC grouping ("Lifestyle", "Household"), or null. */
  group: string | null
  /** "akahu" if it came with the transaction, "genie" if we looked it up. */
  source: 'akahu' | 'genie'
  confidence: number | null
}

export type Merchant = {
  name: string
  id: string | null
  logo: string | null
  website: string | null
}

export type Transaction = {
  id: string
  account_id: string
  /** Already the nickname if the account has one: the server resolves it. */
  account_name: string
  currency: string
  connection_id: string
  /** ISO 8601, UTC. */
  date: string
  description: string
  /** A decimal string; negative is money out. */
  amount: string
  type: string
  merchant: Merchant | null
  category: Category | null
}

export type History = {
  transactions: Transaction[]
  days: number
}

/** Derived from the event log on every read, never stored. See charges/ledger.py. */
export type RequestState = 'open' | 'marked_paid' | 'declined' | 'confirmed' | 'cancelled'

export type RequestEvent = {
  type: string
  /** 'creator' or 'payee'. The creator's actions win. */
  actor: string
  note: string | null
  created_at: string
}

export type ChargeRequest = {
  id: number
  /** The whole address of the request: /r/<token> opens it without an account. */
  token: string
  title: string
  amount_cents: number
  bill_total_cents: number
  payee_email: string
  payee_name: string | null
  from_name: string
  from_email: string
  /** The transaction it was split from, or null if the amount was typed in. */
  source_transaction_id: string | null
  state: RequestState
  created_at: string
  events: RequestEvent[]
}

export type Totals = {
  owed: number
  claimed: number
  settled: number
  /** owed + claimed: money asked for that hasn't been confirmed as arrived. */
  outstanding: number
}

export type Inbox = {
  sent: ChargeRequest[]
  received: ChargeRequest[]
  to_collect: Totals
  to_pay: Totals
}

export type NewPayee = { email: string; name?: string }

/** An invented person to sign in as. Empty in production, where demo is off. */
export type Persona = { email: string; name: string; blurb: string }

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

  /** Blank clears the name. Answers with the whole profile. */
  saveName: (name: string) => request<Me>('/auth/me', 'PATCH', { name }),

  connect: (app_token: string, user_token: string) =>
    request<Connection>('/akahu', 'PUT', { app_token, user_token }),

  disconnect: () => request<void>('/akahu', 'DELETE'),

  selection: () => request<Selection>('/accounts/selection'),

  saveSelection: (included: string[]) =>
    request<Selection>('/accounts/selection', 'PUT', { included }),

  /** Blank puts the bank's own name back. Answers with the whole selection. */
  saveNickname: (id: string, nickname: string) =>
    request<Selection>(`/accounts/${encodeURIComponent(id)}/nickname`, 'PUT', {
      nickname,
    }),

  requests: () => request<Inbox>('/requests'),

  splitBill: (
    title: string,
    amount: string,
    payees: NewPayee[],
    include_me: boolean,
    source_transaction_id?: string,
  ) =>
    request<ChargeRequest[]>('/requests', 'POST', {
      title,
      amount,
      payees,
      include_me,
      source_transaction_id,
    }),

  /** The payer's view. No session needed, which is the point of the link. */
  requestByToken: (token: string) =>
    request<ChargeRequest>(`/requests/r/${encodeURIComponent(token)}`),

  asPayee: (token: string, action: 'mark-paid' | 'decline', note = '') =>
    request<ChargeRequest>(`/requests/r/${encodeURIComponent(token)}/${action}`, 'POST', {
      note,
    }),

  asCreator: (id: number, action: 'confirm' | 'cancel' | 'reopen', note = '') =>
    request<ChargeRequest>(`/requests/${id}/${action}`, 'POST', { note }),

  personas: () => request<Persona[]>('/demo/personas'),

  demoSession: (email: string) => request<Me>('/demo/session', 'POST', { email }),

  transactions: (days: number) => request<History>(`/transactions?days=${days}`),
}

/** The message to put in front of the user when a call fails. */
export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong'
}
