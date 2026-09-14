/**
 * The account and transaction data every signed-in page draws from.
 *
 * The sidebar shows a net balance and a transaction count beside the nav, so
 * this data is no longer one page's business. It outlives any single route.
 * Holding it in one place also means moving between pages doesn't refetch, and
 * the account picker on the settings page updates the dashboard behind it.
 *
 * Created once in App.svelte and read through context, so it can't leak between
 * users and there's no module-level state to reset on sign-out.
 */

import { createContext } from 'svelte'
import { ApiError, api, errorMessage, type Account, type Transaction } from './api'
import { toCents } from './money'

export const RANGES = [
  { days: 30, label: '30 days' },
  { days: 90, label: '3 months' },
  { days: 365, label: '12 months' },
] as const

export const DEFAULT_DAYS = 90

/** Per-currency totals. Adding NZD to AUD would produce a meaningless headline
 *  number, so each currency is counted on its own and shown on its own. */
export type Totals = {
  currency: string
  count: number
  net: number
  assets: number
  owing: number
}

export class Workspace {
  /** Every account Akahu knows about, whether or not it's on the dashboard. */
  accounts = $state.raw<Account[]>([])
  /** The ids ticked for the dashboard. */
  included = $state.raw<string[]>([])
  /** Already filtered to the dashboard accounts. The API does that for us. */
  transactions = $state.raw<Transaction[]>([])
  days = $state<number>(DEFAULT_DAYS)

  /** When the balances on screen were fetched, for the "as at" line. */
  loadedAt = $state.raw<Date | null>(null)

  accountsError = $state('')
  transactionsError = $state('')
  loadingAccounts = $state(false)
  loadingTransactions = $state(false)
  /** False until accounts have answered once, so pages can tell empty from pending. */
  ready = $state(false)

  /** Called when Akahu's tokens have gone away underneath us (a 409). */
  #onExpired: () => void

  constructor(onExpired: () => void) {
    this.#onExpired = onExpired
  }

  dashboardAccounts = $derived(
    this.accounts.filter((account) => this.included.includes(account.id)),
  )

  hiddenCount = $derived(this.accounts.length - this.dashboardAccounts.length)

  totals = $derived.by((): Totals[] => {
    const currencies = [...new Set(this.dashboardAccounts.map((a) => a.currency))]

    return currencies.map((currency) => {
      const cents = this.dashboardAccounts
        .filter((account) => account.currency === currency)
        .map((account) => toCents(account.balance_current))

      return {
        currency,
        count: cents.length,
        net: cents.reduce((sum, value) => sum + value, 0),
        assets: cents.reduce((sum, value) => sum + Math.max(value, 0), 0),
        owing: cents.reduce((sum, value) => sum + Math.min(value, 0), 0),
      }
    })
  })

  /** How many banks are behind those accounts, for the sidebar's summary line. */
  connectionCount = $derived(
    new Set(this.dashboardAccounts.map((a) => a.connection_name)).size,
  )

  /**
   * A 409 means the tokens are gone, which isn't an error to show. It's a
   * signal to start onboarding again. Anything else is worth a message.
   */
  #handle(failure: unknown): string {
    if (failure instanceof ApiError && failure.status === 409) {
      this.#onExpired()
      return ''
    }
    return errorMessage(failure)
  }

  /**
   * Reads the picker's endpoint rather than /accounts: it answers with every
   * account *and* the ticks in one call, which is what the dashboard needs to
   * say how many are hidden and what the settings page needs to draw the list.
   */
  async loadAccounts(): Promise<void> {
    this.loadingAccounts = true
    this.accountsError = ''
    try {
      const selection = await api.selection()
      this.accounts = selection.accounts
      this.included = selection.included
      this.loadedAt = new Date()
    } catch (failure) {
      this.accountsError = this.#handle(failure)
    } finally {
      this.loadingAccounts = false
      this.ready = true
    }
  }

  async loadTransactions(days: number = this.days): Promise<void> {
    this.days = days
    this.loadingTransactions = true
    this.transactionsError = ''
    try {
      this.transactions = (await api.transactions(days)).transactions
    } catch (failure) {
      this.transactionsError = this.#handle(failure)
    } finally {
      this.loadingTransactions = false
    }
  }

  async load(): Promise<void> {
    await Promise.all([this.loadAccounts(), this.loadTransactions()])
  }

  async saveSelection(included: string[]): Promise<void> {
    const selection = await api.saveSelection(included)
    this.accounts = selection.accounts
    this.included = selection.included
    this.loadedAt = new Date()
    // The included set decides which accounts the history covers, so it's
    // stale the moment the ticks change.
    await this.loadTransactions()
  }

  /** New tokens mean a new set of accounts, so everything on screen is stale. */
  async reconnect(appToken: string, userToken: string): Promise<void> {
    await api.connect(appToken, userToken)
    await this.load()
  }

  async disconnect(): Promise<void> {
    await api.disconnect()
    this.accounts = []
    this.included = []
    this.transactions = []
    this.loadedAt = null
    this.ready = false
  }
}

export const [getWorkspace, setWorkspace] = createContext<Workspace>()
