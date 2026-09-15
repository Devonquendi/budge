/**
 * The data every screenshot is taken against.
 *
 * The harness stubs /api outright rather than running FastAPI, so a capture
 * needs no database, no Akahu tokens and no network: the only thing under test
 * is what the browser draws. Balances and dates are therefore fixed, which is
 * what makes two runs on different days comparable.
 */

import type { Page } from '@playwright/test'
import type { History, Me, Selection } from '../src/lib/api.ts'

/**
 * The clock every capture runs on, so "as at" lines and the dashboard's
 * this-month breakdown don't drift. March, and the transactions below sit in
 * the same month in Pacific/Auckland.
 */
export const NOW = new Date('2026-03-14T21:30:00Z')

/** Null logos throughout: a capture shouldn't depend on a bank's CDN. */
const SELECTION: Selection = {
  accounts: [
    {
      id: 'acc_everyday',
      name: 'Everyday',
      type: 'CHECKING',
      connection_name: 'ANZ',
      connection_logo: null,
      formatted_account: '01-0123-0456789-00',
      currency: 'NZD',
      balance_current: '2843.19',
      balance_available: '2843.19',
      nickname: null,
    },
    {
      id: 'acc_savings',
      name: 'Serious Saver',
      type: 'SAVINGS',
      connection_name: 'ANZ',
      connection_logo: null,
      formatted_account: '01-0123-0456789-01',
      currency: 'NZD',
      balance_current: '18250.00',
      balance_available: '18250.00',
      nickname: 'Emergency fund',
    },
    {
      id: 'acc_visa',
      name: 'Visa Platinum',
      type: 'CREDITCARD',
      connection_name: 'ASB',
      connection_logo: null,
      formatted_account: '4835-****-****-2214',
      currency: 'NZD',
      balance_current: '-1204.55',
      balance_available: '6795.45',
      nickname: null,
    },
    {
      id: 'acc_joint',
      name: 'Streamline',
      type: 'CHECKING',
      connection_name: 'ASB',
      connection_logo: null,
      formatted_account: '12-3045-0678901-00',
      currency: 'NZD',
      balance_current: '640.25',
      balance_available: '640.25',
      nickname: null,
    },
    // Left off the dashboard, so the "hidden" count has something to say.
    {
      id: 'acc_old',
      name: 'Everyday',
      type: 'CHECKING',
      connection_name: 'Kiwibank',
      connection_logo: null,
      formatted_account: '38-9012-0345678-00',
      currency: 'NZD',
      balance_current: '12.40',
      balance_available: '12.40',
      nickname: null,
    },
  ],
  included: ['acc_everyday', 'acc_savings', 'acc_visa', 'acc_joint'],
}

type Row = {
  id: string
  account: 'acc_everyday' | 'acc_visa' | 'acc_joint'
  date: string
  description: string
  amount: string
  merchant: string | null
  category: string | null
  group: string | null
  /** Set only for a Genie guess, rather than an Akahu-certain category. */
  guessConfidence?: number
}

const ROWS: Row[] = [
  {
    id: 'trn_01',
    account: 'acc_everyday',
    date: '2026-03-13T21:04:00Z',
    description: 'NEW WORLD THORNDON',
    amount: '-142.86',
    merchant: 'New World',
    category: 'Groceries & supermarkets',
    group: 'Household',
  },
  {
    id: 'trn_02',
    account: 'acc_visa',
    date: '2026-03-13T02:41:00Z',
    description: 'SPOTIFY NZ',
    amount: '-17.99',
    merchant: 'Spotify',
    category: 'Subscriptions',
    group: 'Lifestyle',
  },
  {
    id: 'trn_03',
    account: 'acc_everyday',
    date: '2026-03-12T19:15:00Z',
    description: 'SALARY',
    amount: '2740.00',
    merchant: null,
    category: 'Income',
    group: 'Income',
  },
  {
    id: 'trn_04',
    account: 'acc_visa',
    date: '2026-03-12T04:22:00Z',
    description: 'Z THORNDON QUAY',
    amount: '-88.40',
    merchant: 'Z Energy',
    category: 'Transport & fuel',
    group: 'Transport',
  },
  {
    id: 'trn_05',
    account: 'acc_everyday',
    date: '2026-03-11T23:50:00Z',
    description: 'MERIDIAN ENERGY',
    amount: '-164.20',
    merchant: 'Meridian Energy',
    category: 'Utilities',
    group: 'Household',
  },
  {
    id: 'trn_06',
    account: 'acc_joint',
    date: '2026-03-11T06:33:00Z',
    description: 'RENT WK 11',
    amount: '-620.00',
    merchant: null,
    category: 'Rent',
    group: 'Household',
  },
  {
    id: 'trn_07',
    account: 'acc_visa',
    date: '2026-03-10T01:07:00Z',
    description: 'HAVANA COFFEE WORKS',
    amount: '-11.50',
    merchant: 'Havana Coffee Works',
    category: 'Cafes & restaurants',
    group: 'Lifestyle',
  },
  {
    id: 'trn_08',
    account: 'acc_everyday',
    date: '2026-03-09T20:18:00Z',
    description: 'SNAPPER TOPUP',
    amount: '-40.00',
    merchant: 'Snapper',
    category: 'Public transport',
    group: 'Transport',
  },
  {
    id: 'trn_09',
    account: 'acc_visa',
    date: '2026-03-08T05:44:00Z',
    description: 'MOORE WILSONS',
    amount: '-96.15',
    merchant: "Moore Wilson's",
    category: 'Groceries & supermarkets',
    group: 'Household',
  },
  {
    id: 'trn_10',
    account: 'acc_everyday',
    date: '2026-03-07T02:12:00Z',
    description: 'ONE NZ MOBILE',
    amount: '-49.00',
    merchant: 'One NZ',
    category: 'Phone & internet',
    group: 'Household',
  },
  {
    id: 'trn_11',
    account: 'acc_joint',
    date: '2026-03-06T08:01:00Z',
    description: 'TRANSFER TO SAVINGS',
    amount: '-300.00',
    merchant: null,
    category: null,
    group: null,
  },
  {
    id: 'trn_12',
    account: 'acc_visa',
    date: '2026-03-05T07:26:00Z',
    description: 'THE HANNAH PLAYHOUSE',
    amount: '-72.00',
    merchant: null,
    category: 'Entertainment',
    group: 'Lifestyle',
    guessConfidence: 0.68,
  },
  {
    id: 'trn_13',
    account: 'acc_everyday',
    date: '2026-03-04T21:39:00Z',
    description: 'COUNTDOWN NEWTOWN',
    amount: '-63.74',
    merchant: 'Woolworths',
    category: 'Groceries & supermarkets',
    group: 'Household',
  },
  {
    id: 'trn_14',
    account: 'acc_everyday',
    date: '2026-02-27T19:15:00Z',
    description: 'SALARY',
    amount: '2740.00',
    merchant: null,
    category: 'Income',
    group: 'Income',
  },
  {
    id: 'trn_15',
    account: 'acc_visa',
    date: '2026-03-04T21:41:00Z',
    description: 'MANUKA CAFE & RESTAU 524651******4438 14453 12-14:21-453',
    amount: '-24.00',
    merchant: 'Manuka Cafe & Restaurant',
    category: 'Cafes & restaurants',
    group: 'Lifestyle',
  },
]

const ACCOUNT_NAMES: Record<Row['account'], string> = {
  acc_everyday: 'Everyday',
  acc_visa: 'Visa Platinum',
  acc_joint: 'Streamline',
}

const CONNECTIONS: Record<Row['account'], string> = {
  acc_everyday: 'conn_anz',
  acc_visa: 'conn_asb',
  acc_joint: 'conn_asb',
}

const HISTORY: History = {
  days: 90,
  transactions: ROWS.map((row) => ({
    id: row.id,
    account_id: row.account,
    account_name: ACCOUNT_NAMES[row.account],
    currency: 'NZD',
    connection_id: CONNECTIONS[row.account],
    date: row.date,
    description: row.description,
    amount: row.amount,
    type: row.amount.startsWith('-') ? 'DEBIT' : 'CREDIT',
    merchant: row.merchant
      ? { name: row.merchant, id: null, logo: null, website: null }
      : null,
    category: row.category
      ? {
          name: row.category,
          id: null,
          group: row.group,
          source: row.guessConfidence === undefined ? 'akahu' : 'genie',
          confidence: row.guessConfidence ?? 1,
        }
      : null,
  })),
}

const SIGNED_IN: Me = { email: 'sam@example.com', name: 'Sam', onboarded: true }
const MID_ONBOARDING: Me = { ...SIGNED_IN, onboarded: false }

export type Screen = {
  /** Also the screenshot's filename. */
  name: string
  path: string
  /** Null is signed out, which /auth/me answers with a 401. */
  me: Me | null
  /** The page's <h1>, waited for so a capture can't beat the render. */
  heading: string
}

export const SCREENS: Screen[] = [
  { name: 'login', path: '/login', me: null, heading: 'Welcome back' },
  { name: 'signup', path: '/signup', me: null, heading: 'Create an account' },
  {
    name: 'connect',
    path: '/onboarding',
    me: MID_ONBOARDING,
    heading: 'Connect your banks',
  },
  {
    name: 'choose-accounts',
    path: '/onboarding/accounts',
    me: SIGNED_IN,
    heading: 'Choose your accounts',
  },
  { name: 'dashboard', path: '/', me: SIGNED_IN, heading: 'Dashboard' },
  {
    name: 'transactions',
    path: '/transactions',
    me: SIGNED_IN,
    heading: 'Transactions',
  },
  { name: 'settings', path: '/settings', me: SIGNED_IN, heading: 'Settings' },
  { name: 'profile', path: '/profile', me: SIGNED_IN, heading: 'Profile' },
]

/** Answers every /api call from the fixtures above, so nothing leaves the page. */
export async function stubApi(page: Page, me: Me | null): Promise<void> {
  await page.route('**/api/**', (route) => {
    const path = new URL(route.request().url()).pathname.replace(/^\/api/, '')

    if (path === '/auth/me') {
      return me
        ? route.fulfill({ json: me })
        : route.fulfill({ status: 401, json: { detail: 'Not signed in' } })
    }
    if (path === '/accounts/selection') return route.fulfill({ json: SELECTION })
    if (path === '/transactions') return route.fulfill({ json: HISTORY })

    // Loud rather than empty: a new endpoint should fail the capture, not
    // quietly screenshot a half-drawn page.
    return route.fulfill({ status: 501, json: { detail: `No fixture for ${path}` } })
  })
}
