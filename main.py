# Run: streamlit run main.py

# Imports
import yaml
from PIL import Image
import streamlit as st
from huggingface_hub import hf_hub_download
from langchain.llms import LlamaCpp
from langchain import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferWindowMemory

# Helper
def setup(repo_id:str, filename:str, ai_name:str, user_name:str, context_prompt:str):
  model_path = hf_hub_download(
      resume_download=True,
      cache_dir="models",
      repo_id=repo_id,
      filename=filename,
  )

  kwargs = {
      "model_path": model_path,
      "n_ctx": 4096,
      "max_tokens": 4096,
      "n_batch": 512, 
      "n_gpu_layers": 1
  }
  llm = LlamaCpp(**kwargs)

  context_prompt = PromptTemplate(input_variables=["char","user"], template=context_prompt)
  context_prompt = context_prompt.format(char=ai_name,user=user_name)

  prompt = f"""
  Below is an instruction that describes a roleplay scenario.
  Each of your responses should be in the form of a message that you would send to the other person in the roleplay.

  ### Instruction:
  {context_prompt}

  {"{history}"}
  ### Input:
  {"{input}"}
  ### Response:
  """
  prompt = PromptTemplate(input_variables=["history", "input"], template=prompt)

  memory = ConversationBufferWindowMemory(input_key="input", memory_key="history", k=10)
  memory.ai_prefix = "ASSISTANT"
  memory.human_prefix = "USER"

  conv_chain = ConversationChain(
    llm=llm,
    verbose=False,
    prompt=prompt,
    memory=memory
  )

  return conv_chain

def speak(user_input):
  if 'llm' in st.session_state:
    return st.session_state['llm'].predict(input=user_input)
    
# Setup
try:
  session_state = {}
  with open('conf.yaml', 'r') as file:
    config = yaml.safe_load(file)

  if 'ai_name' not in st.session_state:
    st.session_state['ai_name'] = config['ai']['name']
  if 'user_name' not in st.session_state:
    st.session_state['user_name'] = config['user']['name']
  if 'user_avatar' not in st.session_state:
    st.session_state['user_avatar'] = config['user']['avatar']
  if 'ai_avatar' not in st.session_state:
    st.session_state['ai_avatar'] = config['ai']['avatar']
    
  if "messages" not in st.session_state:
    st.session_state["messages"] = []

  if "favicon" not in st.session_state:
    print(config['favicon'])
    print( Image.open(config['favicon']))
    st.session_state["favicon"] = Image.open(config['favicon'])

  if 'llm' not in st.session_state:
    st.session_state['llm'] = setup(
      repo_id=config['llm']['repo_id'],
      filename=config['llm']['filename'],
      ai_name=config['ai']['name'], 
      user_name=config['user']['name'],
      context_prompt=config['llm']['context_prompt'])
except Exception as e:
  st.error(e)
  st.stop()

# Frontend
st.set_page_config(page_title="Chat with Pirates", page_icon=st.session_state["favicon"])

messages = st.container()
for message in st.session_state["messages"]:
  if message["user"]:
    messages.chat_message(name=st.session_state['user_name'], avatar=st.session_state['user_avatar']).write(message["user"])
  if message["ai"]:
    messages.chat_message(name=st.session_state['ai_name'], avatar=st.session_state['ai_avatar']).write(message["ai"])

prompt = st.chat_input("Say something", key="chat_input")
if prompt and prompt.strip() != "":
  messages.chat_message(name=st.session_state['user_name'], avatar=st.session_state['user_avatar']).write(prompt)
  response = speak(prompt)
  messages.chat_message(name=st.session_state['ai_name'], avatar=st.session_state['ai_avatar']).write(response)
  st.session_state['messages'].append({
    "user": prompt,
    "ai": response,
  })
