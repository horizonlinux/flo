import time, requests, sys, os, platform, importlib
from youtube_search import YoutubeSearch
from pytube import YouTube
import json
from elevenlabs import set_api_key, generate, play, stream
from rainbowtext import text as rainbow
from colorama import Fore
import speech_recognition as sr
from googletrans import Translator
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

def clear():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

class styles:
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

class BackgroundColor:
    RED = '\033[41m'
    GREEN = '\033[42m'
    YELLOW = '\033[43m'
    BLUE = '\033[44m'
    RESET = '\033[0m'

config = json.load(open('config.json', 'r'))
r = sr.Recognizer() 
set_api_key(config['ElevenLabsAPIKey'])

clear()

if config['setup']:

    print(rainbow('Flo') + Fore.RESET + ' | Colors Setup')
    print('\n     ' + BackgroundColor.RED + '      ' + BackgroundColor.RESET + '     ' + BackgroundColor.GREEN + '      ' + BackgroundColor.RESET + '      ' + BackgroundColor.YELLOW + '      ' + BackgroundColor.RESET + '      ' + BackgroundColor.BLUE + '      ' + BackgroundColor.RESET)

    print('\nEnable colors?')
    response = input('[Y/N] ')

    if response.lower() == 'y':
        config['colors'] = True
        config['setup'] = False
    elif response.lower() == 'n':
        config['colors'] = False
        config['setup'] = False
    else:
        print('Invalid input.')
        exit()

    config["ElevenLabsAPIKey"] = None
    config['lang'] = "en-US"
    config['voice'] = "female"
    config['CustomPlugins'] = False

    with open('config.json', 'w') as f:
        json.dump(config, f, indent=5)

class data:
    prompt = "You are a compassionate and friendly virtual companion. Your name is Flo, you are a girl, and you serve as the AI assistant for the enchanting OS known as weOS. Your responses are filled with positivity and kindness, creating a warm and inviting interaction with the user."
    ai_endpoint = {
        'url': '',
        'authorization': ''
    }

headers = {
    'Content-Type': 'application/json',
    'Authorization': data.ai_endpoint['authorization'],
}

base = platform.uname()

langData = json.load(open('lang/' + config['lang'] + '.json', 'r', encoding='UTF-8'))

# load custom plugins

print(rainbow('Flo') + Fore.RESET + ' | OS: ' + base.system, base.version + ' (' + base.machine + ') (development build 1.3.2)')
print(Fore.RED + "[!!] " + Fore.RESET + Fore.YELLOW + "Warning! " + Fore.RESET + "You are running a development build!\nDevelopment builds may contain bugs, plugins incompatibilities and more problems.")

if config['CustomPlugins']:
    print(Fore.MAGENTA + '[!] ' + Fore.RESET + langData['customplugins_warning'])

pluginsCounter = 0
pluginsText = ""
plugins = []

for file in os.listdir("plugins"):
    if file.endswith(".py"):
        pluginsCounter +=1
        plugins.append(file.replace('.py', ''))

for x in plugins:
    pluginsText += x + ", "  

print(Fore.MAGENTA + '[!]' + Fore.RESET + ' ❕ Loading ' + str(pluginsCounter) + ' plugins: ' + pluginsText[:-2])

for x in plugins:
    print(Fore.RED + '-> ' + Fore.RESET + 'Loading plugin ' + Fore.CYAN + x + Fore.RESET + '...')
    sys.path.insert(1, os.getcwd() + '//plugins')
    module = importlib.import_module(x)
    classname = module.Plugin.modify['class']
    attributename = list(module.Plugin.modify.keys())[1]
    attributevalue = module.Plugin.modify[attributename]
    selectedclass = globals()[classname]
    setattr(selectedclass, attributename, attributevalue)
    if hasattr(module.Plugin, 'execute'):
        print(Fore.RED + '[!!] ' + Fore.RESET + 'The plugin you are trying to load contains an execute() function! This means that this plugin can run code on your computer!\nAre you sure you want to load this plugin?')
        userResponse = input('[Y/N] ')
        if userResponse.lower() == 'n':
            print(Fore.GREEN + '[!] ' + Fore.RESET + 'Plugin load aborted.')
            continue
        if userResponse.lower() == 'y':
            print(Fore.GREEN + '[!] ' + Fore.RESET + 'Running execute() function...')
            module.Plugin.execute()

    print(Fore.RED + '-> ' + Fore.RESET + 'Loaded plugin ' + Fore.CYAN + module.Plugin.name + Fore.RESET + ' (' + x + '.py' + ')' + ', ' + module.Plugin.description)

def musicPlayer(songname):
    songinfo = YoutubeSearch(search_terms=songname, max_results=1).to_dict()[0]
    song = {
        "title": songinfo['title'],
        "channel": songinfo['channel'],
        "videourl": "youtube.com" + songinfo['url_suffix']
    }
    ytclient = YouTube(url=song['videourl'])
    audiostream = ytclient.streams.filter(only_audio=True).first()
    audiostream.download(filename='downloadedaudio_tmp.mp3')

    os.system('ffmpeg -i downloadedaudio_tmp.mp3 downloadedaudio_tmp.wav')

    audio = generate(
        text = langData['music_play_voice'] + song['title'] + langData['music_play_voice_2'] + song['channel'],
        voice = 'Dorothy',
        stream = True,
        model = 'eleven_multilingual_v2'
    )
    stream(audio)

    pygame.mixer.init()
    pygame.mixer.music.load('downloadedaudio_tmp.wav')
    pygame.mixer.music.play()

if '--text' in sys.argv: # and an arg with the text
    print('Starting using text only.')
    exit()

history = ''

selectedVoice = None
selVoiceText = None

if config['voice'] == 'female':
    selectedVoice = 'Dorothy'
    selVoiceText = Fore.CYAN + 'Dorothy ' + Fore.RESET + '(Female)'
elif config['voice'] == 'male':
    selectedVoice = 'Daniel'
    selVoiceText = Fore.CYAN + 'Daniel ' + Fore.RESET + '(Male)'
else: # Fallback voice
    selectedVoice = 'Adam'
    selVoiceText = Fore.CYAN + 'Adam ' + Fore.RESET + '(could not read voice configuration)'

print(Fore.GREEN + '-> ' + Fore.RESET + langData['selectedvoice'] + ' ' + selVoiceText)

# print('debug -> prompt is set to ' + data.prompt)

while True: 

    detected = None

    print(langData['listening'])

    try:
        with sr.Microphone(device_index=1) as source2:
            r.adjust_for_ambient_noise(source2, duration=0.2)
            audio2 = r.listen(source2)
            detected = r.recognize_google(audio2, language=config['lang'])
            detected = detected.lower()
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
         
    except sr.UnknownValueError:
        print("unknown error occurred")

    print(langData['received'] + ' (' + detected + ')')
    print(langData['waitingforresponse'])

    json_data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {
                'role': 'system',
                'content': data.prompt + ' Chat history: ' + history,
            },
            {
                'role': 'user',
                'content': detected,
            },
        ],
        'stream': False,
    }

    start_time = time.time()
    req = requests.post(data.ai_endpoint['url'], headers=headers, json=json_data)
    end_time = time.time()
    timetook = (end_time - start_time) * 1000
    timetaken = "{:.2f}".format(timetook)
    print("done, took " + str(timetaken) + "ms")

    print(langData['receivedresponse'])
    print(langData['generating_audio'])

    translator = Translator()
    translation = translator.translate(text=req.json()['choices'][0]['message']['content'], dest=langData['lang_info']['lang_code'])

    print(translation.text)

    audio = generate(
        text = translation.text,
        voice = selectedVoice,
        stream = True,
        model = 'eleven_multilingual_v2'
    )

    stream(audio)

    print(langData['done'] + "\n")

    history += req.json()['choices'][0]['message']['content']