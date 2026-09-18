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

/**
 * Confirming is the only thing worth offering before someone claims to have
 * paid, and money that arrived can't be un-arrived, so a settled request is
 * done. Reopening exists for the case where it wasn't.
 */
export function creatorActions(state: RequestState): ('confirm' | 'cancel' | 'reopen')[] {
  if (state === 'confirmed') return ['reopen']
  if (state === 'cancelled') return ['reopen']
  if (state === 'marked_paid') return ['confirm', 'cancel']
  return ['confirm', 'cancel']
}

export function payeeCanAct(state: RequestState): boolean {
  return state === 'open' || state === 'marked_paid'
}

/** The link to hand someone, absolute so it survives being copied anywhere. */
export function shareUrl(token: string): string {
  return `${window.location.origin}/r/${token}`
}
