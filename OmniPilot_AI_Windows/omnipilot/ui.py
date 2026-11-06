from __future__ import annotations
import queue, threading, tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from PIL import Image, ImageTk
from .config import save_config
from .memory import LocalMemory
from .computer import Computer
from .agent import AutonomousAgent

DARK="#0b0d14"; PANEL="#121622"; PANEL2="#171c2b"; TEXT="#edf0ff"; MUTED="#929bb5"; PURPLE="#8957ff"; BLUE="#36a7ff"; GREEN="#38d996"; RED="#ff657a"
TRANSLATIONS={
 "en":{"title":"OmniPilot AI","tag":"LOCAL · PRIVATE · AUTONOMOUS","task":"Describe a task in English or فارسی…","start":"Start task","pause":"Pause","resume":"Resume","stop":"STOP","settings":"Settings","activity":"Activity log","screen":"Live screen","chat":"Conversation","ready":"Ready · local Ollama","placeholder":"Your computer stays in control. Sensitive actions require confirmation."},
 "fa":{"title":"اُم‌نی‌پایلوت هوش مصنوعی","tag":"محلی · خصوصی · خودکار","task":"درخواست خود را به فارسی یا انگلیسی بنویسید…","start":"شروع کار","pause":"مکث","resume":"ادامه","stop":"توقف فوری","settings":"تنظیمات","activity":"گزارش فعالیت","screen":"نمای زنده صفحه","chat":"گفتگو","ready":"آماده · Ollama محلی","placeholder":"کنترل رایانه با شماست. کارهای حساس نیازمند تأیید هستند."}}

class OmniPilotApp:
    def __init__(self, root: tk.Tk, config: dict):
        self.root=root; self.config=config; self.memory=LocalMemory(Path(__file__).resolve().parent.parent/"omnipilot_memory.sqlite3")
        self.events=queue.Queue(); self.pause_event=threading.Event(); self.stop_event=threading.Event(); self.worker=None; self.awaiting=None; self.pending_approval=None
        self.lang=config.get("language","en"); self._screenshot_ref=None
        self.root.title("OmniPilot AI — Autonomous Desktop Assistant"); self.root.geometry("1260x820"); self.root.minsize(980,650); self.root.configure(bg=DARK)
        self._style(); self._build(); self._poll()
    def _style(self):
        style=ttk.Style(); style.theme_use("clam")
        style.configure("TProgressbar", troughcolor="#252a3b", background=PURPLE, bordercolor="#252a3b", lightcolor=PURPLE, darkcolor=PURPLE)
    def _build(self):
        self.header=tk.Frame(self.root,bg=DARK); self.header.pack(fill="x",padx=22,pady=(18,10))
        brand=tk.Frame(self.header,bg=DARK); brand.pack(side="left")
        tk.Label(brand,text="✦",font=("Segoe UI",27,"bold"),fg=PURPLE,bg=DARK).pack(side="left",padx=(0,10))
        titles=tk.Frame(brand,bg=DARK); titles.pack(side="left")
        self.title_label=tk.Label(titles,text="OmniPilot AI",font=("Segoe UI",20,"bold"),fg=TEXT,bg=DARK); self.title_label.pack(anchor="w")
        self.tag_label=tk.Label(titles,text="LOCAL · PRIVATE · AUTONOMOUS",font=("Segoe UI",8,"bold"),fg=BLUE,bg=DARK); self.tag_label.pack(anchor="w")
        self.settings_btn=self._button(self.header,"⚙  Settings",self.open_settings,subtle=True); self.settings_btn.pack(side="right",padx=5)
        self.lang_btn=self._button(self.header,"فارسی / EN",self.toggle_language,subtle=True); self.lang_btn.pack(side="right",padx=5)
        self.status=tk.Label(self.root,text="Ready · local Ollama",font=("Segoe UI",10),fg=GREEN,bg=DARK,anchor="w"); self.status.pack(fill="x",padx=26,pady=(0,10))
        body=tk.Frame(self.root,bg=DARK); body.pack(fill="both",expand=True,padx=20,pady=2)
        left=tk.Frame(body,bg=PANEL,highlightbackground="#232a3b",highlightthickness=1); left.pack(side="left",fill="both",expand=True,padx=(0,10))
        right=tk.Frame(body,bg=PANEL,highlightbackground="#232a3b",highlightthickness=1,width=450); right.pack(side="right",fill="both",expand=True,padx=(10,0)); right.pack_propagate(False)
        self.chat_head=tk.Label(left,text="Conversation",font=("Segoe UI",11,"bold"),fg=TEXT,bg=PANEL,anchor="w"); self.chat_head.pack(fill="x",padx=16,pady=(14,8))
        self.chat=tk.Text(left,bg=PANEL,fg=TEXT,font=("Segoe UI",10),wrap="word",relief="flat",padx=12,pady=10,insertbackground=TEXT,state="disabled",spacing1=4,spacing3=8)
        self.chat.pack(fill="both",expand=True,padx=8); self.chat.tag_configure("user",foreground="#bfa9ff",justify="right",rmargin=10); self.chat.tag_configure("agent",foreground=TEXT,lmargin1=8); self.chat.tag_configure("system",foreground=MUTED,font=("Segoe UI",9),lmargin1=8)
        self._chat("OmniPilot", "Your computer stays in control. Sensitive actions require confirmation.","system")
        self.progress=ttk.Progressbar(left,mode="determinate",maximum=20); self.progress.pack(fill="x",padx=16,pady=(8,8))
        self.entry=tk.Text(left,height=4,bg=PANEL2,fg=TEXT,font=("Segoe UI",10),wrap="word",relief="flat",padx=11,pady=10,insertbackground=TEXT); self.entry.pack(fill="x",padx=14,pady=(3,8)); self.entry.bind("<Control-Return>",lambda e:(self.start_task(),"break"))
        row=tk.Frame(left,bg=PANEL); row.pack(fill="x",padx=14,pady=(0,14))
        self.start_btn=self._button(row,"Start task",self.start_task,primary=True); self.start_btn.pack(side="left")
        self.pause_btn=self._button(row,"Pause",self.toggle_pause,subtle=True); self.pause_btn.pack(side="left",padx=7)
        self.stop_btn=self._button(row,"STOP",self.stop_task,danger=True); self.stop_btn.pack(side="right")
        self.screen_head=tk.Label(right,text="Live screen",font=("Segoe UI",11,"bold"),fg=TEXT,bg=PANEL,anchor="w"); self.screen_head.pack(fill="x",padx=16,pady=(14,8))
        self.screen=tk.Label(right,text="Screen preview appears when a task starts\n\nWindows 11 desktop capture is required",font=("Segoe UI",10),fg=MUTED,bg="#0a0c12",justify="center"); self.screen.pack(fill="both",expand=True,padx=12,pady=(0,10))
        self.activity_head=tk.Label(right,text="Activity log",font=("Segoe UI",10,"bold"),fg=TEXT,bg=PANEL,anchor="w"); self.activity_head.pack(fill="x",padx=16,pady=(0,4))
        self.log=tk.Text(right,height=8,bg="#0e111a",fg="#b9c2db",font=("Consolas",8),wrap="word",relief="flat",state="disabled",padx=9,pady=6); self.log.pack(fill="x",padx=12,pady=(0,12))
        self.footer=tk.Label(self.root,text="Local inference via Ollama  •  No cloud API  •  Move pointer to a screen corner for PyAutoGUI failsafe",font=("Segoe UI",8),fg=MUTED,bg=DARK); self.footer.pack(fill="x",padx=24,pady=(4,12))
        self.apply_language()
    def _button(self,parent,text,command,primary=False,danger=False,subtle=False):
        bg=RED if danger else PURPLE if primary else PANEL2 if subtle else BLUE
        return tk.Button(parent,text=text,command=command,bg=bg,fg=TEXT,font=("Segoe UI",9,"bold"),relief="flat",bd=0,padx=13,pady=8,activebackground=BLUE,activeforeground="white",cursor="hand2")
    def _chat(self,who,text,tag="agent"):
        self.chat.configure(state="normal"); self.chat.insert("end",f"{who}  ·  {text}\n\n",tag); self.chat.see("end"); self.chat.configure(state="disabled")
    def _log(self,text):
        self.log.configure(state="normal"); self.log.insert("end",text+"\n"); self.log.see("end"); self.log.configure(state="disabled")
    def apply_language(self):
        t=TRANSLATIONS[self.lang]; self.title_label.configure(text=t["title"]); self.tag_label.configure(text=t["tag"]); self.chat_head.configure(text=t["chat"]); self.screen_head.configure(text=t["screen"]); self.activity_head.configure(text=t["activity"])
        self.start_btn.configure(text=t["start"]); self.pause_btn.configure(text=t["resume"] if self.pause_event.is_set() else t["pause"]); self.stop_btn.configure(text=t["stop"]); self.settings_btn.configure(text="⚙  "+t["settings"])
        justify="right" if self.lang=="fa" else "left"
        self.entry.configure(height=4,justify=justify); self.status.configure(anchor="e" if self.lang=="fa" else "w")
        self.chat.tag_configure("user",justify="right"); self.chat.tag_configure("agent",justify=justify); self.chat.tag_configure("system",justify=justify)
        self.chat_head.configure(anchor="e" if self.lang=="fa" else "w"); self.screen_head.configure(anchor="e" if self.lang=="fa" else "w"); self.activity_head.configure(anchor="e" if self.lang=="fa" else "w")
        self.entry.delete("1.0","end"); self.entry.insert("1.0",t["task"])
        self.status.configure(text=t["ready"])
    def toggle_language(self):
        self.lang="fa" if self.lang=="en" else "en"; self.config["language"]=self.lang; save_config(self.config); self.apply_language()
    def start_task(self):
        if self.worker and self.worker.is_alive(): return
        instruction=self.entry.get("1.0","end").strip()
        if instruction in (TRANSLATIONS["en"]["task"],TRANSLATIONS["fa"]["task"]) or not instruction:
            messagebox.showinfo("OmniPilot AI","Enter a task in the request box first."); return
        self.last_instruction=instruction
        self.pause_event.clear(); self.stop_event.clear(); self.pause_btn.configure(text=TRANSLATIONS[self.lang]["pause"]); self.progress.configure(value=0,maximum=self.config["max_steps"])
        self._chat("You",instruction,"user"); self._chat("OmniPilot","Starting task. I will observe the screen, act in bounded steps, and verify results.","agent")
        self.status.configure(text="Starting local agent…",fg=BLUE)
        def emit(kind,data=None): self.events.put((kind,data))
        def approval(prompt,timeout):
            event=threading.Event(); result={}; self.events.put(("approval",(prompt,event,result)))
            if not event.wait(timeout): return None
            return result.get("approved",False)
        def run():
            try:
                computer=Computer(self.config["workspace"],self.config["action_delay_seconds"])
                agent=AutonomousAgent(self.config,computer,emit,approval,self.pause_event,self.stop_event)
                summary=agent.run(instruction)
                emit("finished",("success",summary))
            except Exception as e: emit("finished",("stopped" if self.stop_event.is_set() else "error",str(e)))
        self.worker=threading.Thread(target=run,name="OmniPilotAgent",daemon=True); self.worker.start()
    def toggle_pause(self):
        if not self.worker or not self.worker.is_alive(): return
        if self.pause_event.is_set(): self.pause_event.clear(); self.pause_btn.configure(text=TRANSLATIONS[self.lang]["pause"]); self.status.configure(text="Resuming…",fg=BLUE); self._log("Resumed by user")
        else: self.pause_event.set(); self.pause_btn.configure(text=TRANSLATIONS[self.lang]["resume"]); self.status.configure(text="Paused",fg="#ffd166"); self._log("Paused by user")
    def stop_task(self):
        self.stop_event.set(); self.pause_event.clear()
        if self.pending_approval:
            win,event,result=self.pending_approval
            if not event.is_set(): result["approved"]=False; event.set()
            try: win.destroy()
            except tk.TclError: pass
            self.pending_approval=None
        self.status.configure(text="Stopping safely…",fg=RED); self._log("Emergency STOP requested")
    def _poll(self):
        try:
            while True:
                kind,data=self.events.get_nowait()
                if kind=="approval":
                    prompt,event,result=data
                    self._show_approval(prompt,event,result)
                elif kind=="screenshot":
                    if data:
                        image=Image.open(__import__("io").BytesIO(data)); image.thumbnail((640,390))
                        self._screenshot_ref=ImageTk.PhotoImage(image); self.screen.configure(image=self._screenshot_ref,text="")
                elif kind=="status": self.status.configure(text=str(data),fg=BLUE)
                elif kind=="plan":
                    text="Plan:\n"+"\n".join(f"{i+1}. {s}" for i,s in enumerate(data)); self._chat("OmniPilot",text,"agent"); self._log(text.replace("\n"," · "))
                elif kind=="progress": self.progress.configure(value=data[0],maximum=data[1])
                elif kind=="activity":
                    a=data; safe={k:v for k,v in a.items() if k not in ("content","text")}; self._log("Action: "+str(safe)[:500])
                elif kind=="activity_result": self._log("Result: "+str(data)[:600])
                elif kind=="error": self._log("Warning: "+str(data)); self.status.configure(text=str(data)[:180],fg="#ffd166")
                elif kind=="finished":
                    status,summary=data
                    needs_input=status=="success" and summary.startswith("Clarification needed")
                    label="Clarification required; no action taken." if needs_input else ("Task complete." if status=="success" else ("Stopped." if status=="stopped" else "Task needs attention."))
                    self.status.configure(text=label,fg="#ffd166" if needs_input else (GREEN if status=="success" else RED))
                    self._chat("OmniPilot",summary,"agent"); self.memory.add_task(self.last_instruction if hasattr(self,"last_instruction") else "",summary,"needs_input" if needs_input else status); self._log(f"Task {status}: {summary}")
                    self.pause_event.clear(); self.pause_btn.configure(text=TRANSLATIONS[self.lang]["pause"])
        except queue.Empty: pass
        self.root.after(120,self._poll)
    def _show_approval(self,prompt,event,result):
        win=tk.Toplevel(self.root); win.title("OmniPilot — confirmation required"); win.configure(bg="#191522"); win.geometry("520x300"); win.transient(self.root)
        self.pending_approval=(win,event,result)
        tk.Label(win,text="Sensitive action requires your approval",font=("Segoe UI",12,"bold"),fg="#ffd166",bg="#191522").pack(anchor="w",padx=18,pady=(16,8))
        detail=tk.Text(win,bg="#10131d",fg=TEXT,font=("Segoe UI",10),wrap="word",relief="flat",height=8,padx=10,pady=8); detail.pack(fill="both",expand=True,padx=16,pady=5); detail.insert("1.0",prompt); detail.configure(state="disabled")
        tk.Label(win,text="Review the desktop and action carefully. Decline if uncertain.",font=("Segoe UI",9),fg=MUTED,bg="#191522").pack(anchor="w",padx=18,pady=4)
        row=tk.Frame(win,bg="#191522"); row.pack(fill="x",padx=16,pady=(4,14))
        def finish(approved):
            if event.is_set(): return
            result["approved"]=approved; event.set(); self.pending_approval=None; win.destroy()
        tk.Button(row,text="Decline",command=lambda:finish(False),bg="#34384a",fg=TEXT,relief="flat",padx=14,pady=7).pack(side="right",padx=(7,0))
        tk.Button(row,text="Approve",command=lambda:finish(True),bg=RED,fg="white",relief="flat",padx=14,pady=7).pack(side="right")
        win.protocol("WM_DELETE_WINDOW",lambda:finish(False))
        win.bind("<Escape>",lambda e:finish(False))
    def open_settings(self):
        win=tk.Toplevel(self.root); win.title("OmniPilot settings"); win.configure(bg=DARK); win.geometry("560x540"); win.transient(self.root); win.grab_set()
        tk.Label(win,text="Local AI & workspace settings",font=("Segoe UI",15,"bold"),fg=TEXT,bg=DARK).pack(anchor="w",padx=22,pady=(18,12))
        fields=[("Ollama URL","ollama_url"),("Planner model","planner_model"),("Vision model","vision_model"),("Workspace directory","workspace"),("Maximum actions (1–50)","max_steps"),("Task timeout seconds","task_timeout_seconds")]
        entries={}
        for label,key in fields:
            row=tk.Frame(win,bg=DARK); row.pack(fill="x",padx=22,pady=6)
            tk.Label(row,text=label,width=25,anchor="w",fg=MUTED,bg=DARK,font=("Segoe UI",9)).pack(side="left")
            ent=tk.Entry(row,bg=PANEL2,fg=TEXT,insertbackground=TEXT,relief="flat",font=("Segoe UI",9)); ent.pack(side="left",fill="x",expand=True,ipady=6); ent.insert(0,str(self.config[key])); entries[key]=ent
            if key=="workspace":
                tk.Button(row,text="Browse",command=lambda e=ent:self._browse(e),bg=PANEL2,fg=TEXT,relief="flat").pack(side="right",padx=(5,0))
        tk.Label(win,text="Model requirements: planner text model and vision-language model must both be pulled in Ollama. See README for supported setup.",wraplength=500,justify="left",fg=MUTED,bg=DARK,font=("Segoe UI",9)).pack(anchor="w",padx=22,pady=12)
        buttons=tk.Frame(win,bg=DARK); buttons.pack(fill="x",padx=22,pady=15)
        def save():
            try:
                for key,ent in entries.items():
                    val=ent.get().strip()
                    self.config[key]=int(val) if key in ("max_steps","task_timeout_seconds") else val
                if not self.config["ollama_url"].startswith(("http://127.0.0.1","http://localhost")) and not self.config["ollama_url"].startswith("http://[::1]"):
                    if not messagebox.askyesno("Local endpoint check","This endpoint is not a loopback address. Continue?",parent=win): return
                self.config["workspace"]=str(Path(self.config["workspace"]).expanduser().resolve()); Path(self.config["workspace"]).mkdir(parents=True,exist_ok=True)
                save_config(self.config); messagebox.showinfo("Settings","Settings saved.",parent=win); win.destroy()
            except Exception as e: messagebox.showerror("Settings error",str(e),parent=win)
        self._button(buttons,"Save settings",save,primary=True).pack(side="right"); self._button(buttons,"Cancel",win.destroy,subtle=True).pack(side="right",padx=8)
    def _browse(self,entry):
        value=filedialog.askdirectory(title="Choose OmniPilot workspace")
        if value: entry.delete(0,"end"); entry.insert(0,value)
