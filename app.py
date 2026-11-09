from flask import Flask, request, jsonify, send_from_directory, redirect, session
from pathlib import Path
from datetime import datetime, timezone
import os, json, uuid, hashlib, hmac, tempfile

BASE=Path(__file__).resolve().parent
FRONTEND=BASE/"src"
DB_FILE=Path(os.environ.get("MONEYFLOW_DATA_FILE",str(BASE/"expense-database.json")))
DEFAULT={"users":[],"incomes":[],"expenses":[],"bankAccounts":[],"autopay":[],"goals":[]}
app=Flask(__name__,static_folder=None)
app.secret_key=os.environ.get("MONEYFLOW_SESSION_SECRET") or os.urandom(32)

def now(): return datetime.now(timezone.utc).isoformat()
def load_db():
    if not DB_FILE.exists(): return {k:[] for k in DEFAULT}
    try:
        d=json.loads(DB_FILE.read_text(encoding="utf-8-sig"))
        return {"users":d.get("users",[]),"incomes":d.get("incomes",d.get("income",[])),"expenses":d.get("expenses",[]),"bankAccounts":d.get("bankAccounts",[]),"autopay":d.get("autopay",[]),"goals":d.get("goals",[])}
    except (OSError,json.JSONDecodeError):
        app.logger.exception("Database read failed"); return {k:[] for k in DEFAULT}
def save_db(d):
    DB_FILE.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(dir=DB_FILE.parent,prefix="moneyflow-",suffix=".tmp")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f: json.dump(d,f,indent=2,ensure_ascii=False); f.flush(); os.fsync(f.fileno())
        os.replace(tmp,DB_FILE)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
def pw_hash(p,s): return hashlib.pbkdf2_hmac("sha512",p.encode(),s.encode(),120000,dklen=64).hex()
def clean(u): return {k:u.get(k,"") for k in ("id","name","email","phone","upiId","createdAt","role")}
def out(ok,msg,code=200,**kw): return (jsonify(success=ok,message=msg,**kw),code)
def user_for(d,uid): return next((u for u in d["users"] if str(u.get("id"))==str(uid)),None)
def valid_amount(v):
    try:
        n=float(v); return n if n>0 else None
    except (TypeError,ValueError): return None

@app.get("/")
def home(): return redirect("/login.html")
@app.get("/<path:name>")
def page(name):
    p=(FRONTEND/name).resolve()
    if not str(p).startswith(str(FRONTEND.resolve())+os.sep) or not p.is_file(): return "Not found",404
    return send_from_directory(FRONTEND,name)
@app.get("/health")
def health(): return jsonify(status="ok",app="MoneyFlow")
@app.post("/api/register")
def register():
    x=request.get_json(silent=True) or {}; name=str(x.get("name","")).strip(); email=str(x.get("email","")).strip().lower(); password=str(x.get("password",""))
    if not name or not email or not password: return out(False,"Please fill all required fields.")
    if len(password)<6: return out(False,"Password must contain at least 6 characters.")
    d=load_db()
    if any(u.get("email","").lower()==email for u in d["users"]): return out(False,"An account with this email already exists.")
    salt=os.urandom(16).hex(); u={"id":str(uuid.uuid4()),"name":name,"email":email,"phone":str(x.get("phone","")).strip(),"upiId":"","passwordHash":pw_hash(password,salt),"passwordSalt":salt,"createdAt":now(),"role":"user"}
    d["users"].append(u); save_db(d); return out(True,"Account created successfully.",user=clean(u))
@app.post("/api/login")
def login():
    x=request.get_json(silent=True) or {}; email=str(x.get("email","")).strip().lower(); password=str(x.get("password",""))
    if email=="admin@expense.local" and password=="admin123":
        session["moneyflow_admin"] = True
        return out(True,"Login successful.",user={"id":"moneyflow-demo-admin","name":"Admin","email":email,"phone":"","upiId":"","createdAt":"","role":"admin"})
    d=load_db(); u=next((u for u in d["users"] if u.get("email","").lower()==email),None)
    if not u: return out(False,"Account not found.")
    if not u.get("passwordSalt") or not u.get("passwordHash") or not hmac.compare_digest(pw_hash(password,u["passwordSalt"]),u["passwordHash"]): return out(False,"Incorrect password.")
    return out(True,"Login successful.",user=clean(u))
@app.get("/api/user/<uid>")
def get_user_data(uid):
    d=load_db(); u=user_for(d,uid)
    if not u: return out(False,"User not found.",404)
    result={"success":True,"user":clean(u)}
    for k in ("incomes","expenses","bankAccounts","autopay","goals"): result[k]=[v for v in d[k] if str(v.get("userId"))==str(uid)]
    result["bankTransactions"]=[]; return jsonify(result)
@app.post("/api/<action>")
def mutate(action):
    x=request.get_json(silent=True) or {}; d=load_db(); uid=str(x.get("userId","")); u=user_for(d,uid)
    if action=="update-upi":
        if not u: return out(False,"User not found.")
        u["upiId"]=str(x.get("upiId","")).strip(); save_db(d); return out(True,"UPI ID updated successfully.")
    cfg={"add-income":("incomes","income"),"delete-income":("incomes","income"),"add-expense":("expenses","expense"),"delete-expense":("expenses","expense"),"add-bank-account":("bankAccounts","account"),"update-bank-account":("bankAccounts","account"),"delete-bank-account":("bankAccounts","account"),"add-autopay":("autopay","payment"),"delete-autopay":("autopay","payment"),"add-goal":("goals","goal"),"add-goal-money":("goals","goal"),"delete-goal":("goals","goal")}
    if action not in cfg: return out(False,"Unsupported operation.",404)
    if not u: return out(False,"User not found.")
    key,sing=cfg[action]; arr=d[key]; ident=str(x.get("id",""))
    if action.startswith("delete-"):
        i=next((i for i,v in enumerate(arr) if str(v.get("id"))==ident and str(v.get("userId"))==uid),None)
        if i is None: return out(False,f"{sing.title()} not found.")
        arr.pop(i); save_db(d); return out(True,{"income":"Income deleted.","expense":"Expense deleted.","account":"Bank account deleted.","payment":"AutoPay deleted.","goal":"Savings goal deleted."}[sing])
    if action=="add-goal-money":
        g=next((v for v in arr if str(v.get("id"))==ident and str(v.get("userId"))==uid),None); a=valid_amount(x.get("amount"))
        if not g: return out(False,"Goal not found.")
        if a is None: return out(False,"Enter a valid amount.")
        g["savedAmount"]=min(float(g.get("savedAmount",0))+a,float(g.get("targetAmount",0))); save_db(d); return out(True,"Savings updated successfully.")
    if action=="update-bank-account":
        b=next((v for v in arr if str(v.get("id"))==ident and str(v.get("userId"))==uid),None)
        if not b: return out(False,"Bank account not found.")
        for k in ("bankName","accountHolder","accountType","accountNumber","ifsc","branch","nickname","balance"):
            if k in x: b[k]=x[k]
        b["ifsc"]=str(b.get("ifsc","")).upper(); b["balance"]=float(b.get("balance",0) or 0); save_db(d); return out(True,"Bank account updated successfully.")
    v={"id":str(uuid.uuid4()),"userId":u["id"]}
    if key=="incomes":
        a=valid_amount(x.get("amount"))
        if a is None: return out(False,"Enter a valid income amount.")
        v.update(amount=a,source=str(x.get("source") or "Other"),description=str(x.get("description") or ""),date=x.get("date") or now())
    elif key=="expenses":
        a=valid_amount(x.get("amount"))
        if a is None: return out(False,"Enter a valid expense amount.")
        v.update(amount=a,category=str(x.get("category") or "Other"),description=str(x.get("description") or ""),paymentMethod=str(x.get("paymentMethod") or "Cash"),date=x.get("date") or now())
    elif key=="bankAccounts":
        v.update(bankName=str(x.get("bankName") or "").strip(),accountHolder=str(x.get("accountHolder") or "").strip(),accountType=str(x.get("accountType") or "Savings"),accountNumber=str(x.get("accountNumber") or "").strip(),ifsc=str(x.get("ifsc") or "").strip().upper(),branch=str(x.get("branch") or "").strip(),nickname=str(x.get("nickname") or "").strip(),balance=float(x.get("balance") or 0),createdAt=now())
        if not v["bankName"] or not v["accountNumber"]: return out(False,"Bank name and account number are required.")
    elif key=="autopay":
        a=valid_amount(x.get("amount"))
        if a is None: return out(False,"Enter a valid AutoPay amount.")
        v.update(name=str(x.get("name") or "Subscription"),amount=a,frequency=str(x.get("frequency") or "Monthly"),dueDate=str(x.get("dueDate") or "1"),paymentMethod=str(x.get("paymentMethod") or "UPI"),active=True,createdAt=now())
    elif key=="goals":
        a=valid_amount(x.get("targetAmount"))
        if a is None: return out(False,"Enter a valid target amount.")
        v.update(name=str(x.get("name") or "Savings Goal"),targetAmount=a,savedAmount=0,targetDate=str(x.get("targetDate") or ""),createdAt=now())
    arr.append(v); save_db(d)
    return out(True,{"income":"Income added successfully.","expense":"Expense added successfully.","account":"Bank account added successfully.","payment":"AutoPay added successfully.","goal":"Savings goal created."}[sing],**{sing:v})
@app.get("/api/bank/status")
def bank_status():
    configured = bool(os.environ.get("AA_BASE_URL") and os.environ.get("AA_CLIENT_ID") and os.environ.get("AA_CLIENT_SECRET"))
    return jsonify(success=True, status="online", providerConfigured=configured,
                   message="Account Aggregator provider configured." if configured else "Provider credentials are not configured.")

@app.post("/api/bank/connect")
def bank_connect():
    x = request.get_json(silent=True) or {}
    mobile = "".join(ch for ch in str(x.get("mobile", "")) if ch.isdigit())[-10:]
    if len(mobile) != 10 or mobile[0] not in "6789":
        return out(False, "Enter a valid 10-digit Indian mobile number.", 400)
    if not (os.environ.get("AA_BASE_URL") and os.environ.get("AA_CLIENT_ID") and os.environ.get("AA_CLIENT_SECRET")):
        return out(False, "An authorized Account Aggregator provider is not configured. Add provider credentials and provider-specific consent callback settings in Render.", 503)
    # Implement the selected provider's consent-initiation and callback contract here.
    # Never collect bank passwords, OTPs, CVVs, or UPI PINs in MoneyFlow.
    return out(False, "Provider credentials are present, but the provider-specific consent API and callback must be configured before live connection.", 501)

@app.post("/api/logout")
def logout_api():
    session.clear()
    return out(True, "Signed out.")

@app.get("/api/admin")
def admin_data():
    if not session.get("moneyflow_admin"):
        return out(False, "Administrator access required.", 403)
    d=load_db()
    return jsonify(users=[clean(u) for u in d["users"]],expenses=d["expenses"],income=d["incomes"],bankAccounts=d["bankAccounts"])
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
