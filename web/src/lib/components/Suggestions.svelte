<script lang="ts">
  import { api, errorMessage, type Suggestion } from '../api'
  import { formatCents } from '../money'

  // Money that has arrived and looks like it settles something. Always a
  // question: the matcher declines to guess when a credit is ambiguous, and
  // even a confident match is somebody's word about their own money.
  let { onanswered }: { onanswered: () => void } = $props()

  let items = $state.raw<Suggestion[]>([])
  let busy = $state(0)
  let scanning = $state(false)
  let error = $state('')

  async function load() {
    try {
      items = await api.suggestions()
    } catch (failure) {
      error = errorMessage(failure)
    }
  }

  async function scan() {
    scanning = true
    error = ''
    try {
      await api.scanForPayments()
      await load()
    } catch (failure) {
      error = errorMessage(failure)
    }
    scanning = false
  }

  async function answer(suggestion: Suggestion, reply: 'accept' | 'dismiss') {
    busy = suggestion.id
    error = ''
    try {
      await api.answerSuggestion(suggestion.id, reply)
      await load()
      onanswered()
    } catch (failure) {
      error = errorMessage(failure)
    }
    busy = 0
  }

  const dateOf = (when: string) =>
    new Date(when).toLocaleDateString('en-NZ', { day: 'numeric', month: 'short' })

  load()
</script>

{#if items.length}
  <section>
    <p class="eyebrow">
      Money in that looks like {items.length === 1 ? 'a payment' : 'payments'}
    </p>

    {#each items as suggestion (suggestion.id)}
      <article>
        <p class="what">
          <strong>{formatCents(suggestion.amount_cents, 'NZD')}</strong>
          from <strong>{suggestion.description}</strong>
          on {dateOf(suggestion.occurred_at)}
          matches {suggestion.request.payee_name ?? suggestion.request.payee_email}'s
          share of {suggestion.request.title}.
        </p>
        <div class="answer">
          <button
            type="button"
            disabled={busy === suggestion.id}
            onclick={() => answer(suggestion, 'accept')}
          >
            Yes, that's it
          </button>
          <button
            type="button"
            class="secondary outline"
            disabled={busy === suggestion.id}
            onclick={() => answer(suggestion, 'dismiss')}
          >
            Something else
          </button>
        </div>
      </article>
    {/each}

    {#if error}<p class="error">{error}</p>{/if}
  </section>
{:else}
  <p class="quiet muted">
    Nothing has turned up that matches an open request.
    <button type="button" class="link" disabled={scanning} onclick={scan}>
      {scanning ? 'Checking…' : 'Check my account'}
    </button>
  </p>
  {#if error}<p class="error">{error}</p>{/if}
{/if}

<style>
  section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.75rem 0.875rem;
  }

  article {
    padding: 0.625rem 0.6875rem;
    background: var(--ctp-recessed);
    border-radius: var(--pico-border-radius);
  }

  .what {
    margin: 0;
    font-size: var(--text-label);
    line-height: 1.45;
  }

  .answer {
    display: flex;
    flex-wrap: wrap;
    gap: 0.375rem;
    margin-top: 0.5rem;
  }

  .answer button {
    width: auto;
    margin: 0;
    padding: 0.1875rem 0.625rem;
    font-size: var(--text-meta);
  }

  .quiet {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.375rem;
    margin: 0;
    padding: 0.75rem 0.875rem;
    font-size: var(--text-meta);
  }

  .link {
    width: auto;
    padding: 0;
    background: none;
    border: none;
    font-size: var(--text-meta);
    color: var(--pico-muted-color);
    text-decoration: underline;
  }
</style>
