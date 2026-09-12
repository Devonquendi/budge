function formatCurrency(amount, currency) {
  return new Intl.NumberFormat("en-NZ", { style: "currency", currency }).format(amount);
}

async function loadAccounts() {
  const response = await fetch("/api/accounts");
  if (response.status === 409) {
    location.href = "/onboarding";
    return [];
  }
  if (!response.ok) throw new Error(`Failed to load accounts: ${response.status}`);
  return response.json();
}

function renderAccounts(accounts) {
  const body = document.getElementById("accounts-body");
  body.replaceChildren();

  for (const account of accounts) {
    const row = document.createElement("tr");
    for (const value of [account.name, account.connection_name, account.type]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.appendChild(cell);
    }

    const balanceCell = document.createElement("td");
    balanceCell.className = "balance";
    if (account.balance_current < 0) balanceCell.classList.add("negative");
    balanceCell.textContent = formatCurrency(account.balance_current, account.currency);
    row.appendChild(balanceCell);

    body.appendChild(row);
  }

  const total = accounts.reduce((sum, account) => sum + account.balance_current, 0);
  const currency = accounts[0]?.currency ?? "NZD";
  const totalEl = document.getElementById("total-balance");
  totalEl.textContent = formatCurrency(total, currency);
  totalEl.removeAttribute("aria-busy");
}

loadAccounts()
  .then(renderAccounts)
  .catch((error) => {
    const body = document.getElementById("accounts-body");
    body.replaceChildren();
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    cell.colSpan = 4;
    cell.textContent = `Couldn't load accounts: ${error.message}`;
    row.appendChild(cell);
    body.appendChild(row);
  });
