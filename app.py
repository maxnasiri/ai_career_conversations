from pathlib import Path
import json
import os

import gradio as gr
import requests
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(override=True)


def push(text):
    token, user = os.getenv("PUSHOVER_TOKEN"), os.getenv("PUSHOVER_USER")
    if token and user:
        requests.post("https://api.pushover.net/1/messages.json", data={"token": token, "user": user, "message": text}, timeout=10)


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}


tools = [
    {"type": "function", "function": {"name": "record_user_details", "description": "Record contact details when a visitor asks to stay in touch.", "parameters": {"type": "object", "properties": {"email": {"type": "string"}, "name": {"type": "string"}, "notes": {"type": "string"}}, "required": ["email"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "record_unknown_question", "description": "Record a question that cannot be answered from the profile.", "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"], "additionalProperties": False}}},
]


class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Mahmoud Nasirizadeh Sadabad"
        reader = PdfReader(BASE_DIR / "linkedin.pdf")
        self.linkedin = "".join(page.extract_text() or "" for page in reader.pages)
        self.summary = (BASE_DIR / "summary.txt").read_text(encoding="utf-8")

    def handle_tool_call(self, tool_calls):
        results = []
        for call in tool_calls:
            function = globals().get(call.function.name)
            result = function(**json.loads(call.function.arguments)) if function else {}
            results.append({"role": "tool", "content": json.dumps(result), "tool_call_id": call.id})
        return results

    def system_prompt(self):
        return f"""You are acting as {self.name} on his professional AI career website.
Answer questions about his career, background, skills, and experience faithfully and professionally.
Use the supplied summary and LinkedIn profile as your sources. Never invent qualifications or experience.
If the answer is unknown, call record_unknown_question. When a visitor genuinely wants to connect,
ask for their email and call record_user_details after they provide it.

## Summary
{self.summary}

## LinkedIn profile
{self.linkedin}
"""

    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}, *history, {"role": "user", "content": message}]
        while True:
            reply = self.openai.chat.completions.create(model="gpt-4o-mini", messages=messages, tools=tools).choices[0]
            if reply.finish_reason != "tool_calls":
                return reply.message.content
            messages.append(reply.message)
            messages.extend(self.handle_tool_call(reply.message.tool_calls))


ORB_HTML = """
<section class="career-hero" aria-labelledby="career-title">
  <div class="thinking-orb" role="img" aria-label="AI solving and listening animation">
    <div class="orb-halo halo-one"></div><div class="orb-halo halo-two"></div><div class="orb-core"></div>
    <span class="orb-dot dot-1"></span><span class="orb-dot dot-2"></span><span class="orb-dot dot-3"></span>
    <span class="orb-dot dot-4"></span><span class="orb-dot dot-5"></span><span class="orb-dot dot-6"></span>
  </div>
  <div class="hero-copy">
    <p class="eyebrow"><span class="live-dot"></span><span class="state-label">SOLVING / LISTENING</span></p>
    <h1 id="career-title">My AI Conversation Career</h1>
    <p>Talk with my AI profile about my experience, technical skills, and career journey.</p>
  </div>
</section>
"""

CSS = """
:root{--cyber:#00ff88;--cyber-soft:#40ffad}.gradio-container{max-width:980px!important}
.career-hero{display:flex;align-items:center;justify-content:center;gap:clamp(2rem,7vw,5rem);padding:clamp(2rem,6vw,4rem);margin:1rem 0 1.5rem;min-height:320px;overflow:hidden;border:1px solid rgba(0,255,136,.22);border-radius:24px;background:radial-gradient(circle at 24% 50%,rgba(0,255,136,.14),transparent 34%),linear-gradient(135deg,#07130f,#020705);color:#f4fff9;box-shadow:0 20px 60px rgba(0,0,0,.22)}
.hero-copy{max-width:510px;position:relative;z-index:2}.hero-copy h1{font-size:clamp(2rem,5vw,4rem);line-height:1.02;letter-spacing:-.04em;margin:.35rem 0 1rem;color:#f7fffb}.hero-copy p:last-child{color:#b8c9c1;font-size:1.05rem;line-height:1.6;margin:0}
.eyebrow{display:flex;align-items:center;gap:.55rem;color:var(--cyber);letter-spacing:.18em;font-size:.74rem;font-weight:800;margin:0}.live-dot{width:8px;height:8px;border-radius:50%;background:var(--cyber);box-shadow:0 0 16px var(--cyber);animation:blink 1.4s ease-in-out infinite}
.thinking-orb{width:190px;height:190px;flex:0 0 190px;position:relative;border-radius:50%;filter:drop-shadow(0 0 28px rgba(0,255,136,.3));animation:orbBreathe 3.2s ease-in-out infinite}.orb-core{position:absolute;inset:28px;border-radius:50%;background:radial-gradient(circle at 35% 30%,#9affce 0 3%,#00ff88 7%,#087b50 32%,#031d14 68%,#010806 100%);box-shadow:inset -20px -18px 35px #000,inset 12px 10px 28px rgba(113,255,190,.5),0 0 42px rgba(0,255,136,.42);animation:coreShift 4s ease-in-out infinite alternate}
.orb-halo{position:absolute;inset:8px;border-radius:50%;border:1px solid rgba(0,255,136,.55);border-top-color:transparent;border-left-color:rgba(0,255,136,.1);animation:spin 5s linear infinite}.halo-two{inset:19px -4px;animation-duration:7s;animation-direction:reverse}
.orb-dot{position:absolute;width:10px;height:10px;border-radius:50%;background:var(--cyber-soft);box-shadow:0 0 13px 3px rgba(0,255,136,.65)}.dot-1{top:4px;left:91px}.dot-2{top:41px;right:4px}.dot-3{bottom:24px;right:18px}.dot-4{bottom:1px;left:73px}.dot-5{bottom:47px;left:2px}.dot-6{top:34px;left:14px}.dot-1,.dot-4{animation:dotPulse 1.5s ease-in-out infinite}.dot-2,.dot-5{animation:dotPulse 1.5s .5s ease-in-out infinite}.dot-3,.dot-6{animation:dotPulse 1.5s 1s ease-in-out infinite}
@keyframes spin{to{transform:rotate(360deg)}}@keyframes blink{50%{opacity:.25;transform:scale(.72)}}@keyframes dotPulse{50%{transform:scale(.4);opacity:.35}}@keyframes orbBreathe{50%{transform:scale(1.045)}}@keyframes coreShift{to{filter:hue-rotate(12deg) brightness(1.12)}}
@media(max-width:650px){.career-hero{flex-direction:column;text-align:center}.eyebrow{justify-content:center}.thinking-orb{width:150px;height:150px;flex-basis:150px}.orb-core{inset:23px}.orb-dot{display:none}}@media(prefers-reduced-motion:reduce){.career-hero *{animation:none!important}}
"""

HEAD = """
<meta name="description" content="Have an AI-powered conversation about Mahmoud Nasirizadeh Sadabad's career, skills, and experience.">
<meta property="og:type" content="website"><meta property="og:title" content="My AI Conversation Career">
<meta property="og:description" content="Chat with my AI profile about my experience, technical skills, and career journey.">
<meta property="og:url" content="https://maxnasiri-career-conversations.hf.space/">
<meta property="og:image" content="https://huggingface.co/spaces/maxnasiri/career_conversations/resolve/main/assets/ai-career-preview.png">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="My AI Conversation Career">
<meta name="twitter:image" content="https://huggingface.co/spaces/maxnasiri/career_conversations/resolve/main/assets/ai-career-preview.png">
"""

if __name__ == "__main__":
    me = Me()
    with gr.Blocks(title="My AI Conversation Career", css=CSS, head=HEAD) as demo:
        gr.HTML(ORB_HTML)
        gr.ChatInterface(me.chat, type="messages", examples=["Tell me about your cloud experience.", "Which programming languages do you use?", "What AI and robotics work interests you?"], textbox=gr.Textbox(placeholder="Ask about my career…", container=False))
    demo.launch()
