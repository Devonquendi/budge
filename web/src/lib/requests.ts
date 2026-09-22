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

export function payeeCanAct(state: RequestState): boolean {
  return state === 'open' || state === 'marked_paid'
}

/** The link to hand someone, absolute so it survives being copied anywhere. */
export function shareUrl(token: string): string {
  return `${window.location.origin}/r/${token}`
}
