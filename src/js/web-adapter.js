// Browser API bridge for MoneyFlow's frontend.
(() => {
  async function request(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok && data.success !== false) throw new Error('Request failed (' + response.status + ')');
    return data;
  }
  const post = (action, data) => request('/api/' + action, {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data || {})});
  const get = url => request(url);
  window.MoneyFlow = {
    loginUser: d => post('login',d), registerUser: d => post('register',d),
    getUserData: id => get('/api/user/' + encodeURIComponent(id)),
    updateUPI: d => post('update-upi',d), addIncome: d => post('add-income',d), deleteIncome: d => post('delete-income',d),
    addExpense: d => post('add-expense',d), deleteExpense: d => post('delete-expense',d),
    addBankAccount: d => post('add-bank-account',d), updateBankAccount: d => post('update-bank-account',d), deleteBankAccount: d => post('delete-bank-account',d),
    addAutoPay: d => post('add-autopay',d), deleteAutoPay: d => post('delete-autopay',d),
    addGoal: d => post('add-goal',d), addGoalMoney: d => post('add-goal-money',d), deleteGoal: d => post('delete-goal',d),
    getAllData: () => get('/api/admin')
  };
})();