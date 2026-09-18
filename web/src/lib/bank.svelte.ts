/**
 * Whether this deployment has the stand-in bank on it.
 *
 * One-tap is offered in two places and neither should assume: a real
 * deployment has no bank to send anyone to, and a button that leads nowhere is
 * worse than no button. Asked once, shared by both.
 */

import { api } from './api'

const state = $state({ present: false, asked: false })

export function hasBank(): boolean {
  return state.present
}

export async function check(): Promise<void> {
  if (state.asked) return
  state.asked = true
  try {
    // The personas and the stand-in bank are the same switch: both are the demo.
    state.present = (await api.personas()).length > 0
  } catch {
    state.present = false
  }
}
