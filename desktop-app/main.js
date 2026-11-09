const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const db = require("./database");
let mainWindow;
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1450, height: 900, minWidth: 1100, minHeight: 700,
    backgroundColor: "#07111f",
    webPreferences: { preload: path.join(__dirname, "preload.js"), contextIsolation: true, nodeIntegration: false },
    show: false
  });
  mainWindow.loadFile(path.join(__dirname, "..", "src", "login.html"));
  mainWindow.once("ready-to-show", () => mainWindow.show());
  mainWindow.on("closed", () => { mainWindow = null; });
}
const handlers = {
  "register-user": data => db.registerUser(data),
  "login-user": data => db.loginUser(data),
  "get-user-data": id => db.getUserData(id),
  "add-income": data => db.addIncome(data),
  "delete-income": data => db.deleteIncome(data),
  "add-expense": data => db.addExpense(data),
  "delete-expense": data => db.deleteExpense(data),
  "update-upi": data => db.updateUPI(data),
  "add-bank-account": data => db.addBankAccount(data),
  "update-bank-account": data => db.updateBankAccount(data),
  "delete-bank-account": data => db.deleteBankAccount(data),
  "add-autopay": data => db.addAutoPay(data),
  "delete-autopay": data => db.deleteAutoPay(data),
  "add-goal": data => db.addGoal(data),
  "add-goal-money": data => db.addGoalMoney(data),
  "delete-goal": data => db.deleteGoal(data)
};
for (const [channel, handler] of Object.entries(handlers)) {
  ipcMain.handle(channel, async (_event, data) => {
    try { return handler(data); }
    catch (error) { return { success: false, message: error.message }; }
  });
}
ipcMain.handle("show-message", async (_event, data) => {
  await dialog.showMessageBox(mainWindow, { type: data.type || "info", title: data.title || "MoneyFlow", message: data.message || "" });
  return { success: true };
});
app.whenReady().then(() => {
  createWindow();
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) createWindow(); });
});
app.on("window-all-closed", () => { if (process.platform !== "darwin") app.quit(); });