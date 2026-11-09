/* Browser compatibility adapter replacing Electron preload/IPC. */
(() => {
  async function post(action,data) {
    const r=await fetch("/api/"+action,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(data||{})});
    return await r.json();
  }
  const api={
    registerUser:d=>post("register",d), loginUser:d=>post("login",d),
    getUserData:async id=>(await fetch("/api/user/"+encodeURIComponent(id))).json(),
    addIncome:d=>post("add-income",d), deleteIncome:d=>post("delete-income",d),
    addExpense:d=>post("add-expense",d), deleteExpense:d=>post("delete-expense",d),
    updateUPI:d=>post("update-upi",d),
    addBankAccount:d=>post("add-bank-account",d), updateBankAccount:d=>post("update-bank-account",d), deleteBankAccount:d=>post("delete-bank-account",d),
    addAutoPay:d=>post("add-autopay",d), deleteAutoPay:d=>post("delete-autopay",d),
    addGoal:d=>post("add-goal",d), addGoalMoney:d=>post("add-goal-money",d), deleteGoal:d=>post("delete-goal",d),
    showMessage:d=>{alert((d&&d.message)||"");return Promise.resolve({success:true});}
  };
  window.moneyflow=api;
  window.expenseAPI={getUserData:api.getUserData,getAllData:async()=>(await fetch("/api/admin")).json(),addBankAccount:api.addBankAccount,updateBankAccount:api.updateBankAccount,deleteBankAccount:api.deleteBankAccount};
})();
