/** How a request's state reads, and what can still be done to it. */

import type { RequestState } from './api'

type Look = { label: string; tone: 'open' | 'claimed' | 'good' | 'bad' }

const LOOKS: Record<RequestState, Look> = {
  open: { label: 'Waiting', tone: 'open' },
  marked_paid: { label: 'Says paid', tone: 'claimed' },
  confirmed: { label: 'Settled', tone: 'good' },
  declined: { label: 'Declined', tone: 'bad' },
  cancelled: { label: 'Cancelled', tone: 'bad' },
}

export function look(state: RequestState): Look {
  return LOOKS[state]
}

/** A payer who declined can still change their mind and pay. */
export function payeeCanPay(state: RequestState): boolean {
  return state === 'open' || state === 'declined'
}

export function payeeCanDecline(state: RequestState): boolean {
  return state === 'open' || state === 'marked_paid'
}

export function payeeCanAct(state: RequestState): boolean {
  return payeeCanPay(state) || payeeCanDecline(state)
}

/** The link to hand someone, absolute so it survives being copied anywhere. */
export function shareUrl(token: string): string {
  return `${window.location.origin}/r/${token}`
}
