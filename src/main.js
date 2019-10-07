import axios from 'axios'

document.querySelector('#faucetForm').addEventListener('submit', (event) => {
  event.preventDefault()
  const account = document.querySelector('#recipientAddress').value
  const resultEl = document.querySelector('#result')
  const explorerUrl = document.querySelector('#explorer_url').value
  const topupAmount = document.querySelector('#topup_amount').value
  showResult(resultEl)
  document.querySelector('#result').innerHTML = ` <div class="flex flex-col">
                                                    <img src="/assets/images/cycle-loader.svg" class="inline-block">
                                                    <div class="font-mono inline-block text-center mt-4">Adding ${topupAmount} AE to:<br>
                                                      <strong class="mt-4 inline-block text-xs">${account}</strong>
                                                    </div>
                                                  </div>`
  axios.post('/account/' + account)
    .then(function (response) {
      resultEl.innerHTML = `<strong>Added ${topupAmount} AE!</strong><br>
      <br>Current Balance: <strong> ${(response.data.balance / 1000000000000000000)} AE </strong><br>
      <br>Transaction: <a class="text-purple font-mono text-xs" href="${explorerUrl}/transactions/${response.data.tx_hash}" target="_blank">${response.data.tx_hash}</a><br>
      <br>Account: <a class="text-purple font-mono text-xs" href="${explorerUrl}/account/transactions/${account}" target="_blank">${account}</a>`
    })
    .catch(function (error) {
      resultEl.innerHTML = `Something went wrong. ¯\\_(ツ)_/¯  <br>
      ${error.response.data.message}<br>
      Please try again later.`
      console.log(error)
    })
})
const showResult = function (resultEl) {
  const className = 'hidden'
  if (resultEl.classList) {
    resultEl.classList.remove('hidden', 'lg:hidden')
  } else {
    resultEl.className = resultEl.className.replace(new RegExp('(^|\\b)' + className.split(' ').join('|') + '(\\b|$)', 'gi'), ' ')
  }
}
