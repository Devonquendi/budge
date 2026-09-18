<script lang="ts">
  import { api, errorMessage, type Suggestion } from '../api'
  import { formatCents } from '../money'

  // Only what the app could not settle on its own. A credit that could only be
  // one thing closes its request without asking, so anything here is genuinely
  // uncertain and worth a person's attention.
  let { onanswered }: { onanswered: () => void } = $props()

  let items = $state.raw<Suggestion[]>([])
  let busy = $state(0)
  let scanning = $state(false)
  let error = $state('')

  let settledJustNow = $state(0)

  async function load() {
    try {
      items = await api.suggestions()
    } catch (failure) {
      error = errorMessage(failure)
    }
  }

  /** Reads the feed on the way in, so settling is something that just happens. */
  async function sweep() {
    try {
      const scan = await api.scanForPayments()
      settledJustNow = scan.settled
      if (scan.settled) onanswered()
    } catch {
      // A bank that will not answer should not stop the page loading.
    }
    await load()
  }

  async function scan() {
    scanning = true
    error = ''
    try {
      const result = await api.scanForPayments()
      settledJustNow = result.settled
      if (result.settled) onanswered()
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

  sweep()
</script>

{#if items.length}
  <section>
    <p class="eyebrow">
      {items.length === 1 ? 'One payment' : `${items.length} payments`} we couldn't be sure
      about
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
    {#if settledJustNow}
      Settled {settledJustNow}
      {settledJustNow === 1 ? 'request' : 'requests'} from money that arrived. Nothing left
      to check.
    {:else}
      Nothing needs your say-so. Payments that can only be one thing settle themselves.
    {/if}
    <button type="button" class="link" disabled={scanning} onclick={scan}>
      {scanning ? 'Checking…' : 'Check again'}
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
