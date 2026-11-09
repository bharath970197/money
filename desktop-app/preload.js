const { contextBridge, ipcRenderer } = require("electron");
const channels = ["register-user","login-user","get-user-data","add-income","delete-income","add-expense","delete-expense","update-upi","add-bank-account","update-bank-account","delete-bank-account","add-autopay","delete-autopay","add-goal","add-goal-money","delete-goal","show-message"];
const api = {};
for (const channel of channels) {
  const method = channel.replace(/-([a-z])/g, (_m, c) => c.toUpperCase());
  api[method] = data => ipcRenderer.invoke(channel, data);
}
contextBridge.exposeInMainWorld("moneyflow", api);