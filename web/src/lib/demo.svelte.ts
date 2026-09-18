/**
 * Whether this deployment is the demo.
 *
 * Three things hang off it: the stand-in bank one-tap sends people to, and the
 * sign-in page, which should lead with the invented people rather than a
 * password box no demo account has a password for.
 *
 * Asked once. The personas endpoint answers it without a session, which the
 * public request page needs.
 */

import { api } from './api'

const state = $state({ present: false, asked: false })

export function isDemo(): boolean {
  return state.present
}

/** Kept as its own name because this is what the caller actually means. */
export function hasBank(): boolean {
  return state.present
}

export async function check(): Promise<void> {
  if (state.asked) return
  state.asked = true
  try {
    state.present = (await api.personas()).length > 0
  } catch {
    state.present = false
  }
}
